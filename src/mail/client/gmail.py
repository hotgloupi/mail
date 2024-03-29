import itertools
import re
import imaplib
imaplib._MAXLINE = 100000

from .base import BaseClient
from mail import message

class AuthenticationError(Exception):
    pass

def split_seq(seq, size):
    """ Split up seq in pieces of size (stolen from http://gumuz.looze.net)"""
    return [seq[i:i+size] for i in range(0, len(seq), size)]

class Client(BaseClient):

    type = 'gmail'

    imap_host = 'imap.gmail.com'
    imap_port = 993
    mailbox_name = 'INBOX'

    def login(self):
        if not self.imap:
            self.connect()
        try:
            imap_login = self.imap.login(self.account.email, self.account.password)
            self.logged_in = (imap_login and imap_login[0] == 'OK')
        except imaplib.IMAP4.error:
            raise AuthenticationError()
        self.imap.select(self.mailbox_name)

    def fetch_message_ids(self):
        res, data = self.imap.uid('search', None, 'ALL')
        if res != 'OK':
            raise Exception("Cannot fetch mails")
        return map(int, data[0].decode('utf8').split(' '))

    def fetch_messages(self, ids):
        for some_ids in split_seq(ids, 50):
            for msg in self._fetch_messages(some_ids):
                yield msg

    def _fetch_messages(self, ids):
        response, result = self.imap.uid(
            'FETCH',
            ','.join(map(str, ids)),
            '(BODY.PEEK[] FLAGS X-GM-THRID X-GM-MSGID X-GM-LABELS)'
        )
        if response != 'OK':
            raise Exception("Cannot fetch messages: " + response)
        for part in result:
            if not isinstance(part, tuple):
                continue
            header = part[0].decode('utf8')
            remote_id = int(re.search('UID (\d+)', header).group(1))
            gmail_thread_id = int(re.search('X-GM-THRID (\d+)', header).group(1))
            gmail_message_id = int(re.search('X-GM-THRID (\d+)', header).group(1))
            flags = [
                ('thread-id', '%s-%s' % (self.account.id, gmail_thread_id)),
                ('message-id', '%s-%s' % (self.account.id, gmail_message_id)),
            ]
            gmail_flags = re.search("FLAGS \(([^)]*)\)", header).group(1)
            seen = False
            for f in gmail_flags.split():
                if f == '\\Seen':
                    seen = True

            flags.append(('seen', seen and 'true' or 'false'))
            gmail_labels = re.search("X-GM-LABELS \(([^)]*)\)", header).group(1)
            flags.extend(('label', l.strip('"').replace('\\\\', '\\')) for l in gmail_labels.split(' ') if l)
            yield message.parse(
                conn = self.conn,
                account = self.account,
                remote_id = remote_id,
                mailbox = self.mailbox,
                flags = flags,
                raw_data = part[1],
            )

    def fetch_message(self, id):
        for msg in self.fetch_messages([id]):
            return msg # We return the first one (if any)
