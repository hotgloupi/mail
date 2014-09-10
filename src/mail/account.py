from mail import db
import json

class Account:

    def __init__(self, id, email, type, **kw):
        self.id = id
        self.email = email
        self.type = type
        self.__dict__.update(kw)


def all(cursor = None):
    if cursor == None:
        cursor = db.conn().cursor()
    cursor.execute("SELECT id, email, type, authentication FROM account")
    res = []
    for row in cursor.fetchall():
        res.append(Account(row[0], row[1], row[2], **json.loads(row[3])))
    return res
