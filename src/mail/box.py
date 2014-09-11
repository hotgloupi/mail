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


class Box:

    def __init__(self,
                 account,
                 name = None,
                 labels = None,
                 id = None):
        assert id is not None or (None not in (name, labels)),\
                "Either id or both name and labels must be given"
        self.account = account
        self.name = name
        self.labels = labels
        self.id = id


    def _find_id(self, conn):
        curs.execute(
            "SELECT id FROM mailbox WHERE name = ? AND account_id = ?",
            (self.name, self.account.id)
        )
        res = curs.fetchone()
        if res:
            return res[0]

    def _fetch(conn):
        """Fetch name and labels from DB"""
        curs.execute(
            "SELECT name FROM mailbox WHERE id = ?", (self.id, )
        )
        self.name = curs.fetchone()[0]
        curs.execute(
            """
            SELECT value FROM mailbox_flag
            WHERE mailbox_id = ? AND key = 'label'
            """,
            (self.id, )
        )
        self.labels = []
        for row in curs.fetchall():
            self.labels.append(row[0])

    def _update(conn):
        """Update name and labels in DB"""
        curs.execute(
            "UPDATE mailbox SET name = ? WHERE id = ?",
            (self.name, self.id)
        )
        assert self.labels is not None
        curs.execute(
            """
            DELETE FROM mailbox_flag
            WHERE mailbox_id = ? and key = 'label'
            """,
            (self.id, )
        )
        for label in self.labels:
            curs.execute(
                """
                INSERT INTO mailbox_flag (mailbox_id, key, value)
                VALUES (?, 'label', ?)
                """,
                (self.id, label)
            )

    def _insert(self, conn):
        """Let's save the new mailbox in DB"""
        curs.execute(
            "INSERT INTO mailbox (id, name, account_id) VALUES (NULL, ?, ?)",
            (self.name, self.account.id)
        )
        self.id = curs.lastrowid
        for label in self.labels:
            curs.execute(
                """
                INSERT INTO mailbox_flag (mailbox_id, key, value)
                VALUES (?, 'label', ?)
                """,
                (self.id, label)
            )

    def synchronize(self, conn):
        curs = conn.cursor()
        if self.id is None:
            self.id = self._find_id(conn)
        if self.id is not None: # The box already exists in DB
            if self.name is None:
                self._fetch(conn)
            else:
                self._update(conn)
        else:
            self._insert(conn)
        curs.commit()
        return self

def parse(box):
    pass
