import subprocess
import argparse
import os

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-reply')
    parser.add_argument(
        'mail',
        help = 'Mail to reply to',
        nargs = '+',
    )
    parser.add_argument(
        '--all', '-a',
        help = 'Reply to all',
        action = 'store_true',
    )
    return parser.parse_args(args)

from mail import object, message, db

def run(args):
    conn = db.conn()
    for uid in args.mail:
        if not object.is_object(uid):
            print("'%s' is not a valid object" % uid)
            return 1
        if object.get_kind(uid) != 'mail':
            print("'%s' does not refer to a mail" % uid)
        mail = message.fetch_one(conn, object.get_id(uid))
        with open('/tmp/lol.eml', 'w') as f:
            f.write("From: %s\n" % mail.account.email)
            f.write("To: %s\n" % mail.sender)
            f.write("Subject: %s\n" % mail.pretty_subject)
            f.write('\n\n')
            f.write("## This line and the lines below won't be included.\n")
            f.write("## Just move text that you wish to be included above the previous line.\n")
            f.write("## The three first line (From, To and Subject) are purely informative.\n")
            f.write("## Recipients, sender, subject, attachments are modifiable later.\n")
            f.write('\n')
            for line in mail.render(conn.cursor(), mode = 'text', width = 72):
                if line:
                    print('>', line, file = f)
                else:
                    print('>', file = f)

        subprocess.call([os.getenv('EDITOR'), '/tmp/lol.eml'])


        with open('/tmp/lol.eml') as f:
            start = True
            lines = []
            for line in f:
                if start:
                    if line.startswith('From: ') or \
                       line.startswith('To: ') or \
                       line.startswith('Subject: '):
                        continue
                if line.startswith('## '): break
                start = False
                lines.append(line.strip('\n'))
        def is_whitespace(line):
            return all((c in ' \r\t\n') for c in line)
        if all(is_whitespace(line) for line in lines):
            print("Empty reply, aborting")
            return 1
        for line in lines:
            print(line)
