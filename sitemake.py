"""# Site Generator Script:
~0325hrs IST, 28th Oct 2023

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


from typing import List, Dict, Tuple
from pathlib import Path, PosixPath


CURDIR_PATH = Path.cwd()
EXEC_PATH = Path(__file__).parent.absolute()


def parse_target_files(dir_path: str) -> Tuple[Dict, Dict]:
    PathObj = Path(dir_path)
    cur_level = dir_path
    file_level_map = {}
    dir_list = []
    file_list = []
    code_files = {}

    for item in PathObj.iterdir():
        if item.name[0] == ".":
            continue
        # breakpoint()
        if item.is_dir():
            dir_list.append(item)
        elif item.is_file():
            file_list.append(item)

    # recursive traversal here to get all the paths and file items
    for dir_item in dir_list:
        file_list.extend(parse_target_files(dir_item))

    for file_item in file_list:
        if not isinstance(file_item, PosixPath):
            continue
        file_level_map[str(file_item.relative_to(CURDIR_PATH))] = str(cur_level)
        if file_item.suffix == ".py":
            code_files[str(file_item.relative_to(CURDIR_PATH))] = file_item.name

        # breakpoint()
    return file_level_map, code_files


def generate_nav(nav_map: dict = {}) -> Dict:
    return {}


def generate_site():
    # static site component stuff will go here
    pass


def main():
    print(CURDIR_PATH)
    print(EXEC_PATH)
    dir_map, code_files = parse_target_files(CURDIR_PATH)
    print(json.dumps(dir_map, indent=4))
    print(json.dumps(code_files, indent=4))


if __name__ == "__main__":
    main()
