import email
import email.parser
import json

from . import db

class Message:

    def __init__(self,
                 account,
                 remote_id,
                 content,
                 id = None):
        self.id = id
        self.remote_id = remote_id
        self.account = account
        self.content = content

    def save(self, conn = None):
        if conn is None:
            conn = db.conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mail (id, account_id, remote_id) VALUES (?, ?, ?)",
            (self.id, self.account.id, self.remote_id)
        )
        if self.id is None:
            self.id = cursor.lastrowid
        for headers, type, body in self.content:
            if isinstance(body, bytes):
                table = 'binary_content'
            else:
                table = 'text_content'
            cursor.execute(
                """
                INSERT INTO %s (mail_id, headers, content_type, payload)
                VALUES (?, ?, ?, ?)
                """ % table,
                (self.id, json.dumps(headers), type, body)
            )
        conn.commit()


def get_message_content(msg):
    content = []
    for idx, part in enumerate(msg.walk()):
        charset = part.get_content_charset()
        type = part.get_content_type()
        headers = list(map(str, part.items()))
        body = part.get_payload(decode = True)
        if body is not None and charset is not None:
            body = body.decode(charset, 'replace')
        content.append((headers, type, body))
    return content

def parse(conn, account, remote_id, raw_data):
    msg = email.message_from_bytes(raw_data)
    return Message(account, remote_id, get_message_content(msg))

