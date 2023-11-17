import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_MICROPYTHON_SRC = DIRECTORY_OF_THIS_FILE.parent.parent /"software"/ "micropython"
assert DIRECTORY_MICROPYTHON_SRC.is_dir(),DIRECTORY_MICROPYTHON_SRC

FILES_PATTERN = "list_files = ()"
def create_package():
    for f in DIRECTORY_MICROPYTHON_SRC.glob("*.py"):
        print(f.name)



if __name__ == "__main__":
    create_package()