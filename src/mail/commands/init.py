import argparse
import os
import pathlib
import sqlite3

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-init')
    parser.add_argument(
        'directory',
        help = 'Root directory for your mails',
        default = '.',
        type = pathlib.Path,
        action = 'store',
        nargs = '?'
    )
    parser.add_argument(
        '--force', '-f',
        help = 'Force initialization',
        action = 'store_true'
    )
    return parser.parse_args(args)

def run(args):
    dir = (args.directory / '.mail').absolute()
    print("Initializing mail in", dir)
    if dir.is_dir():
        if not args.force:
            print("The directory", dir, "already exists, use --force")
            return 1
    else:
        dir.mkdir()

    conn = sqlite3.connect(str(dir / 'db.sqlite3'))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY NOT NULL,
            email TEXT,
            type TEXT,
            authentication TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mail (
            id INTEGER PRIMARY KEY NOT NULL,
            account_id INTEGER,
            remote_id TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS text_content (
            mail_id INTEGER NOT NULL,
            headers TEXT,
            content_type TEXT,
            payload TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS binary_content (
            mail_id INTEGER NOT NULL,
            headers TEXT,
            content_type TEXT,
            payload BLOB
        )
        """
    )
