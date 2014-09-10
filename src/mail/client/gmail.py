import itertools
import re
import imaplib
imaplib._MAXLINE = 100000

from .base import BaseClient
from mail import message

class AuthenticationError(Exception):
    pass

class Client(BaseClient):

    type = 'gmail'

    imap_host = 'imap.gmail.com'
    imap_port = 993

    def login(self):
        if not self.imap:
            self.connect()
        try:
            imap_login = self.imap.login(self.account.email, self.account.password)
            self.logged_in = (imap_login and imap_login[0] == 'OK')
        except imaplib.IMAP4.error:
            raise AuthenticationError()
        self.imap.select('INBOX')

    def fetch_message_ids(self):
        res, data = self.imap.uid('search', None, 'ALL')
        if res != 'OK':
            raise Exception("Cannot fetch mails")
        return map(int, data[0].decode('utf8').split(' '))

    def fetch_messages(self, ids):
        response, result = self.imap.uid('FETCH', ','.join(map(str, ids)), '(RFC822)')
        if response != 'OK':
            raise Exception("Cannot fetch messages: " + response)
        messages = {}
        for part in result:
            if not isinstance(part, tuple):
                continue
            match = re.search('UID (\d+)', part[0].decode('utf8'))
            if not match:
                print("Ignore non-matching result", part)
                continue

            id = int(match.group(1))
            messages[id] = message.parse(
                conn = self.conn,
                account = self.account,
                remote_id = id,
                raw_data = part[1]
            )
        return messages

    def fetch_message(self, id):
        try:
            return self.fetch_messages([id])[id]
        except KeyError:
            return None
