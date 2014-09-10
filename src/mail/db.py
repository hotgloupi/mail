import sqlite3

from mail import box

def conn(config_directory = None):
    if config_directory is None:
        config_directory = box.find_config_directory()
    return sqlite3.connect(str(config_directory / 'db.sqlite3'))
