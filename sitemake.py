"""TextBlock
# Site Generator Script:
Created: ~0325hrs IST, 28th Oct 2023

I started writing this script first as a standalone module, then thought about
working with it as a full-fledged Python module that I could build and maybe
even package as a single unit. That led me nowhere, so I briefly considered
pursuing golang or rust to build this as a binary that I could just drop into
the dir containing my notes and have it generate a blog, but that made no 
sense either.

Finally, I think I have a solution that makes sense. What I want to do is
to embed content into Python files directly as ReStructured Text in 
doctring-style string blocks, and then use these to form the bodies of the
text. I can then think about embedding the code between text content or 
something, or maybe making it so that I can set the strings as variables
and reference them in some Python-compliant way that doesn't affect the code,
but makes sense in context of the text.

Why do this at all? I think there's some sense in making code more literate
in some ways that don't have to do with the programming paradigms used to
compose the code in the first place. Also, working like this allows more
dynamic use of Python's abilities to compose or alter the text, or to imbue
values in the text at publishing time, or embed external content with better
ease. Also, I don't know right now if this will work. So, yeah.

And this script should be able to fulfil that role, so I can maybe start
actually writing and stop ruminating so much.
"""

import json
import logging
import os
import shutil
import signal
import sys

from collections import defaultdict
from docutils.core import publish_parts
from markdown import markdown
from pathlib import Path, PosixPath
from rst2html5_ import HTML5Writer
from typing import List, Dict, Tuple

SUPPORTED_TYPES = {".py", ".rst", ".md"}
CURDIR_PATH = Path.cwd()
EXEC_PATH = Path(__file__).parent.absolute()
if CURDIR_PATH == EXEC_PATH:
    OUTPUT_PATH = Path(os.path.join(CURDIR_PATH, "output"))
    SOURCE_PATH = Path(os.path.join(CURDIR_PATH, "source"))
else:
    OUTPUT_PATH, SOURCE_PATH = CURDIR_PATH, CURDIR_PATH
BASE_TEMPLATE_PATH = Path(os.path.join(CURDIR_PATH, "template/base.html"))
BASE_TEMPLATE_STYLE_N_SCRIPT = (
    Path(os.path.join(CURDIR_PATH, "template/style.css")),
    Path(os.path.join(CURDIR_PATH, "template/script.js")),
)

logger = logging.getLogger("sitemake")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def parse_source_files(dir_path: str) -> Tuple[Dict, Dict]:
    PathObj = Path(dir_path)
    dir_list = []
    file_list = []
    paths_dir_map = defaultdict(list)

    for item in PathObj.iterdir():
        if item.name[0] == ".":
            continue
        if item.is_dir():
            dir_list.append(item)
        elif item.is_file():
            file_list.append(item)

    # recursive traversal here to get all the paths and file items
    for dir_item in dir_list:
        subdir_paths_dir_map = parse_source_files(dir_item)
        for k, v in subdir_paths_dir_map.items():
            paths_dir_map[k].extend(v)
    for file_item in file_list:
        if not isinstance(file_item, PosixPath):
            continue
        if file_item.suffix.lower() in {".py", ".md", ".rst"}:
            logger.debug("valid file: ", file_item.name)
            dir_rel_path = str(file_item.parent.relative_to(CURDIR_PATH))
            paths_dir_map[dir_rel_path].append(file_item.name)
    logger.debug(paths_dir_map)
    return paths_dir_map


def clear_output_directory(output_base_dir: Path):
    dir_list = []
    file_list = []
    paths_dir_map = defaultdict(list)
    for item in output_base_dir.iterdir():
        if item.is_dir():
            dir_list.append(item)
        elif item.is_file():
            file_list.append(item)

    # recursive traversal here to get all the paths and file items
    for dir_item in dir_list:
        clear_output_directory(dir_item)
        os.rmdir(dir_item)
    for file_item in file_list:
        if not isinstance(file_item, PosixPath):
            raise Exception("Could not delete file, Invalid filepath: {}".format(str(file_item)))
        else:
            os.remove(file_item)

    logger.debug(paths_dir_map)
    return


def handle_file_parse(inpath: Path, outpath: Path):
    base_template_html = BASE_TEMPLATE_PATH.read_text()
    if inpath.suffix in (".rst", ".py"):
        html = publish_parts(writer=HTML5Writer(), source=inpath.read_text())["body"]
    else:
        parsed_doc = inpath.read_text()
        html = markdown(parsed_doc)
    outpath.write_text(base_template_html.format(body_content=html))
    pass


def generate_output_paths(output_base_dir, source_map: Dict[str, str]):
    if not output_base_dir.exists():
        os.makedirs(output_base_dir)
    for path in BASE_TEMPLATE_STYLE_N_SCRIPT:
        op_name = os.path.join(
            output_base_dir, path.name
        )  # TODO add code here to copy the css and js file into the output folder
        shutil.copy(path, op_name)

    output_map = {}
    for dir, file_list in source_map.items():
        output_dir_path = Path(os.path.join(CURDIR_PATH, f"output{dir[6:]}"))
        if not output_dir_path.exists():
            os.makedirs(output_dir_path)

        for filename in file_list:
            source_file_path = "/".join(
                (
                    dir,
                    filename,
                )
            )
            source_file_path_abs = os.path.realpath(source_file_path)
            output_path_object = Path(os.path.join(output_dir_path, filename))
            output_path_object.touch()
            output_path_object = output_path_object.rename(output_path_object.with_suffix(".html"))
            handle_file_parse(Path(source_file_path_abs), output_path_object)
            output_map[str(output_path_object)] = source_file_path_abs
    return output_map


# TODO: first create directories, then generate nav, then populate files, and finally use
# nav to verify that all files have been created
def generate_nav(output_base_dir, output_map: dict = {}) -> Dict:
    nav_map = defaultdict(Dict)
    nav_abspath = lambda x: f"Index/{os.path.relpath(x, output_base_dir)}"
    nav_list = [nav_abspath(k) for k in output_map.keys()]
    return nav_list


def parse_dir_paths(project_path):
    # static site component stuff will go here
    paths_dir_map = parse_source_files(project_path)
    logger.info(json.dumps(paths_dir_map, indent=4))

    project_path_obj = Path(project_path)
    output_dir = Path(os.path.join(OUTPUT_PATH, project_path_obj.name))
    return paths_dir_map, output_dir


def confirm_source_path(possible_paths: tuple) -> int:
    while True:
        print("Choose a project by num:")
        input_args = "\n".join(
            [" ".join((f"{i[0] + 1}. ", i[1])) for i in enumerate(possible_paths)],
        )
        check_path = input(f"{input_args} \nProject num ->: ")
        if check_path.isnumeric() and 0 < int(check_path) <= len(possible_paths):
            return possible_paths[int(check_path) - 1]
        else:
            print("Invalid input.")
            continue


def setup_output():
    print(f"Current path: {str(CURDIR_PATH)}")
    print(f"Sitemake path: {str(EXEC_PATH)}")
    if not OUTPUT_PATH.exists():
        print("OUTPUT dir does not exist. Creating...")
        OUTPUT_PATH.mkdir()
    print(f"OUTPUT path: {str(OUTPUT_PATH)}")
    if not SOURCE_PATH.exists():
        print("TARGET dir does not exist. Creating...")
        SOURCE_PATH.mkdir()
    print(f"TARGET path: {str(SOURCE_PATH)}")

    print("Checking source path contents...")
    source_list = list(str(i) for i in SOURCE_PATH.iterdir() if i.is_dir())
    source_path = confirm_source_path(source_list)
    return source_path


def main():
    source_project = setup_output()
    source_paths, output_base_dir = parse_dir_paths(source_project)
    if output_base_dir.exists():
        clear_output_directory(output_base_dir)
        os.rmdir(output_base_dir)
    output_paths = generate_output_paths(output_base_dir, source_paths)
    nav = generate_nav(output_base_dir, output_paths)


def handle_signal(sig, frame):
    print("\nHandled SIGINT\nExiting now...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_signal)


if __name__ == "__main__":
    print("Print Ctrl+C to exit")
    main()
