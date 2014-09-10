import email
import email.parser
import email.utils
import json
from datetime import datetime

from . import db, contact

class Message:

    def __init__(self,
                 account,
                 remote_id,
                 content,
                 subject,
                 sender,
                 recipients,
                 date,
                 id = None):
        self.id = id
        self.remote_id = remote_id
        self.account = account
        self.content = content
        self.subject = subject
        self.sender = sender
        self.recipients = recipients
        self.date = date

    def save(self, conn = None):
        if conn is None:
            conn = db.conn()
        if self.sender is not None:
            self.sender.synchronize(conn)
            sender_id = self.sender.id
        else:
            sender_id = None
        for recipient in self.recipients:
            recipient.synchronize(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mail (id, account_id, remote_id, subject, sender_id, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.id, self.account.id, self.remote_id, self.subject, sender_id, self.date)
        )
        if self.id is None:
            self.id = cursor.lastrowid
        for recipient in self.recipients:
            cursor.execute(
                "INSERT INTO mail_recipient (mail_id, recipient_id) VALUES (?, ?)",
                (self.id, recipient.id)
            )
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


def extract_message_content(msg):
    content = []
    for idx, part in enumerate(msg.walk()):
        charset = part.get_content_charset()
        type = part.get_content_type()
        headers = list(map(str, part.items()))
        body = part.get_payload(decode = True)
        if body is not None and charset is not None:
            if charset.startswith('charset='):
                charset = charset[8:].strip('"') # XXX Stupid parsing bug
            body = body.decode(charset, 'replace')
        content.append((headers, type, body))
    return content

def decode_header(text):
    fragments = []
    for frag, charset in email.header.decode_header(text):
        if not isinstance(frag, str):
            try_list = []
            if charset is not None and charset not in ['unknown-8bit']:
                try_list.append(charset)
            try_list.extend(['ascii', 'utf8', 'latin-1'])
            for charset in try_list:
                try:
                    frag = frag.decode(charset)
                except:
                    charset = None
                else:
                    break
            if charset is None:
                raise Exception("Cannot decode %s" % subject)
        fragments.append(frag)
    return ''.join(fragments)

def extract_sender(conn, msg):
    senders = list(map(str, msg.get_all('From', [])))
    pass

def extract_contacts(conn, msg, headers):
    addresses = []
    for k in headers:
        addresses.extend(map(str, msg.get_all(k, [])))
    addresses = email.utils.getaddresses(addresses)
    result = []
    for name, mail in addresses:
        result.append(
            contact.Contact(mail = mail, fullname = decode_header(name))
        )
    return result

def extract_date(msg):
    date_tuple = email.utils.parsedate_tz(str(msg['Date']))
    if date_tuple:
        return datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))

def parse(conn, account, remote_id, raw_data):
    msg = email.message_from_bytes(raw_data)
    #for k,v in msg.items():
    #    print(" - %s: %s" % (str(k), str(v)))
    senders = extract_contacts(conn, msg, ['From'])
    if senders:
        sender = senders[0]
    else:
        sender = None
    return Message(
        account,
        remote_id,
        content = extract_message_content(msg),
        subject = decode_header(msg['Subject'] or ''),
        recipients = extract_contacts(
            conn, msg, ['To', 'Cc', 'Cci', 'Resend-To']
        ),
        sender = sender,
        date = extract_date(msg),
    )

def fetch(conn,
          account = None,
          offset = 0,
          count = 50):
    curs = conn.cursor()
    curs.execute(
        """
        SELECT id FROM mail
        WHERE sender_id is not null
        ORDER BY date DESC
        LIMIT %d OFFSET %d
        """ % (count, offset)
    )
    for row in curs.fetchall():
        yield fetch_one(conn, account, row[0])

def fetch_one(conn, account, id):
    curs = conn.cursor()
    curs.execute(
        """SELECT id, remote_id, sender_id, subject, date
        FROM mail WHERE id = ?""",
        (id, )
    )
    res = curs.fetchone()
    if res:
        return Message(
            account = account,
            id = res[0],
            remote_id = res[1],
            sender = contact.Contact(id = res[2]).synchronize(conn),
            recipients = [],
            subject = res[3],
            date = res[4],
            content = None,
        )

def find_one(conn, account, remote_id = None):
    curs = conn.cursor()
    if remote_id is not None:
        curs.execute(
            "SELECT id FROM mail WHERE account_id = ? AND remote_id = ?",
            (account.id, remote_id)
        )
        res = curs.fetchone()
        if res:
            return fetch_one(conn, account, res[0])

def exists(conn, account, remote_id = None):
    curs = conn.cursor()
    if remote_id is not None:
        curs.execute(
            "SELECT id FROM mail WHERE account_id = ? AND remote_id = ?",
            (account.id, remote_id)
        )
        return curs.fetchone() and True or False
