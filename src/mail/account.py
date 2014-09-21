from mail import db
import json

class Account:

    def __init__(self, id, email = None, type = None, **kw):
        self.id = id
        self.email = email
        self.type = type
        self.__dict__.update(kw)

    def load(self, conn):
        curs = conn.cursor()
        curs.execute(
            "SELECT email, type, authentication FROM account WHERE id = ?",
            (self.id, )
        )
        row = curs.fetchone()
        self.email = row[0]
        self.type = row[1]
        self.__dict__.update(json.loads(row[2]))
        return self


def all(cursor = None):
    if cursor == None:
        cursor = db.conn().cursor()
    cursor.execute("SELECT id, email, type, authentication FROM account")
    res = []
    for row in cursor.fetchall():
        res.append(Account(row[0], row[1], row[2], **json.loads(row[3])))
    return res
