import imaplib

import mail
from mail import box

class BaseClient:
    type = None
    imap_host = None
    imap_port = None
    default_mailbox_name = 'INBOX'

    def __init__(self, conn, account):
        assert self.type is not None, "Subclass must specify a type"
        assert account.type == self.type, "Wrong account"
        self.account = account
        self.conn = conn
        self.imap = None
        self.logged_in = False
        self.__mailbox_name = self.default_mailbox_name
        self.__mailbox = None

    def connect(self):
        self.imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)

    def mailboxes(self):
        res, boxes = self.imap.list()
        if res != 'OK':
            raise Exception("Cannot get mailboxes")
        return [
            mail.box.parse(box, self.account) for box in boxes
        ]

    @property
    def mailbox(self):
        if self.__mailbox is None:
            self.__mailbox = box.Box(
                account = self.account,
                name = self.__mailbox_name,
            ).synchronize(self.conn)
        assert self.__mailbox is not None
        return self.__mailbox

    @property
    def mailbox_name(self):
        return self.__mailbox_name

    @mailbox_name.setter
    def mailbox_name(self, value):
        assert isinstance(value, str)
        if value == self.__mailbox_name: return
        try:
            self.__mailbox = box.Box(
                account = self.account,
                name = value,
            ).synchronize(self.conn)
        except:
            raise
        else:
            self.__mailbox_name = value
        return self.__mailbox_name
