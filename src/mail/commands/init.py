import os
import pathlib
import sqlite3

arguments = [
    dict(
        flags = 'directory',
        help = 'Root directory for your mails',
        default = '.',
        type = pathlib.Path,
        action = 'store',
        nargs = '?'
    ),
    dict(
        flags = ('--force', '-f'),
        help = 'Force initialization',
        action = 'store_true'
    ),
]

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
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY NOT NULL,
            email TEXT,
            fullname TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS contact_id ON contact (id)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mail (
            id INTEGER PRIMARY KEY NOT NULL,
            account_id INTEGER REFERENCES account (id),
            mailbox_id INTEGER REFERENCES mailbox (id),
            remote_id TEXT UNIQUE,
            sender_id INTEGER REFERENCES contact (id),
            subject TEXT,
            date DATETIME
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS mail_id ON mail (id)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mail_recipient (
            mail_id INTEGER REFERENCES mail (id),
            recipient_id INTEGER REFERENCES contact (id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS mail_recipient_mail_id ON mail_recipient (mail_id)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS text_content (
            mail_id INTEGER REFERENCES mail (id),
            headers TEXT,
            content_type TEXT,
            payload TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS text_content_mail_id ON text_content (mail_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS binary_content (
            mail_id INTEGER REFERENCES mail (id),
            headers TEXT,
            content_type TEXT,
            payload BLOB
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS binary_content_mail_id ON binary_content (mail_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS external_content (
            uri TEXT PRIMARY KEY NOT NULL,
            content_type TEXT,
            payload BLOB
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS uri ON external_content (uri)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS thread (
            id INTEGER PRIMARY KEY NOT NULL,
            remote_id TEXT UNIQUE
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mail_flag (
            mail_id INTEGER REFERENCES mail (id),
            key TEXT,
            value TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mailbox (
            id INTEGER PRIMARY KEY NOT NULL,
            name TEXT,
            account_id INTEGER REFERENCES account (id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mailbox_flag (
            mailbox_id INTEGER REFERENCES mailbox (id),
            key TEXT,
            value TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS staged (
            object TEXT,
            action TEXT,
            arguments TEXT
        )
        """
    )
