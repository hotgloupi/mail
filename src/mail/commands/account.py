import argparse
import hashlib
import getpass
import json

from mail import box, db

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-account')
    subparsers = parser.add_subparsers(dest = 'action')
    add = subparsers.add_parser('add', help = 'Add an account')
    add.add_argument(
        'email',
        help = "E-mail of the account",
    )
    return parser.parse_args(args)


def add_gmail(conn, args):
    pw = getpass.getpass()
    data = json.dumps({'password': pw})
    conn.execute(
        "INSERT INTO account (id, email, type, authentication) VALUES (NULL, ?, ?, ?)",
        (args.email, 'gmail', data)
    )
    conn.commit()

def add(conn, args):
    if args.email.endswith('@gmail.com'):
        add_gmail(conn, args)
    else:
        print("Unknown mail address provider")
        return 1

def run(args):
    conn = db.conn()
    if args.action == 'add':
        return add(conn, args)
