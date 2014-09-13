import os
import pathlib

from . import utf7

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
                 flags = None,
                 id = None):
        assert id is not None or name is not None
        self.account = account
        self.name = name
        self.flags = flags
        self.id = id

    def _find_id(self, curs):
        curs.execute(
            "SELECT id FROM mailbox WHERE name = ? AND account_id = ?",
            (self.name, self.account.id)
        )
        res = curs.fetchone()
        if res:
            return res[0]

    def _fetch(self, curs):
        """Fetch name and flags from DB"""
        curs.execute(
            "SELECT name FROM mailbox WHERE id = ?", (self.id, )
        )
        self.name = curs.fetchone()[0]
        curs.execute(
            """
            SELECT value FROM mailbox_flag
            WHERE mailbox_id = ? AND key = 'flag'
            """,
            (self.id, )
        )
        self.flags = [row[0] for row in curs.fetchall()]
        return self

    def _update(self, curs):
        """Update name and flags in DB"""
        curs.execute(
            "UPDATE mailbox SET name = ? WHERE id = ?",
            (self.name, self.id)
        )
        assert self.flags is not None
        curs.execute(
            """
            DELETE FROM mailbox_flag
            WHERE mailbox_id = ? and key = 'flag'
            """,
            (self.id, )
        )
        for flag in self.flags:
            curs.execute(
                """
                INSERT INTO mailbox_flag (mailbox_id, key, value)
                VALUES (?, 'flag', ?)
                """,
                (self.id, flag)
            )
        return self

    def _insert(self, curs):
        """Let's save the new mailbox in DB"""
        curs.execute(
            "INSERT INTO mailbox (id, name, account_id) VALUES (NULL, ?, ?)",
            (self.name, self.account.id)
        )
        self.id = curs.lastrowid
        if self.flags is None:
            return self
        for flag in self.flags:
            curs.execute(
                """
                INSERT INTO mailbox_flag (mailbox_id, key, value)
                VALUES (?, 'flag', ?)
                """,
                (self.id, flag)
            )
        return self

    def synchronize(self, conn):
        curs = conn.cursor()
        if self.id is None:
            self.id = self._find_id(curs)
        if self.id is not None:      # The box already exists in DB
            if None in (self.name, self.flags):
                self._fetch(curs)
            else:
                self._update(curs)
        else:
            self._insert(curs)
        conn.commit()
        return self

    def __str__(self):
        return "<Box {name} ({id}) %s>".format(**self.__dict__) % ' '.join(self.flags)

def all(account, cursor = None):
    if cursor is None:
        cursor = db.conn().cursor()
    cursor.execute("SELECT id FROM mailbox")
    for row in cursor.fetchall():
        yield Box(account, id = row[0])._fetch(cursor)

def parse(box, account):
    box = utf7.decode(box)
    flags, name = map(lambda s: s.strip('() "'), box.split('"/"'))
    flags = flags.split()
    return Box(account, name = name, flags = flags)
