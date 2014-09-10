import os
import pathlib

class ConfigDirectoryNotFound(Exception):
    pass

def find_config_directory(start = None):
    if start is None:
        start = pathlib.Path(os.getcwd())
    assert isinstance(start, pathlib.Path)
    while not (start / '.mail').is_dir():
        if str(start) == str(start.anchor):
            raise ConfigDirectoryNotFound()
        start = start.parent
    return start / '.mail'


