import imaplib

import mail

class BaseClient:
    type = None
    imap_host = None
    imap_port = None

    def __init__(self, conn, account):
        assert self.type is not None, "Subclass must specify a type"
        assert account.type == self.type, "Wrong account"
        self.account = account
        self.conn = conn
        self.imap = None
        self.logged_in = False

    def connect(self):
        self.imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)

    def mailboxes(self):
        res, boxes = self.imap.list()
        if res != 'OK':
            raise Exception("Cannot get mailboxes")
        return [
            mail.box.parse(box) for box in boxes
        ]
