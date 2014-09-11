import argparse

from mail import db, account, client, message, pager

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-fetch')
    return parser.parse_args(args)

def run(args):
    conn = db.conn()
    for msg in message.fetch(conn, count = 200):
        subject = msg.subject.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        while '  ' in subject:
            subject = subject.replace('  ', ' ')
        print(msg.date, msg.sender.fullname or msg.sender.mail, '[%s]' % subject)

