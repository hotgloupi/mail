import argparse

from mail import db, account, client, message

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-fetch')
    return parser.parse_args(args)

def run(args):
    conn = db.conn()
    for msg in message.fetch(conn):
        print(msg.date, msg.sender.mail, msg.subject)
