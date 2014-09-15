import argparse

from mail import db, account, client, message, pager, format

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-fetch')
    return parser.parse_args(args)

def run(args):
    conn = db.conn()
    for msg in message.fetch(conn, count = 20):
        subject = msg.subject.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        while '  ' in subject:
            subject = subject.replace('  ', ' ')
        print(
            "%s %-15s %-20s %s" % (
                msg.uid,
                format.pretty_date(msg.date),
                msg.sender.fullname or msg.sender.mail,
                subject,
            )
        )

