import argparse

from mail import db, account, client, message

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-fetch')
    return parser.parse_args(args)

def run(args):
    conn = db.conn()
    all = account.all(conn.cursor())
    if not all:
        print('You must add accounts first')
        return 1

    for acc in all:
        cl = client.make(conn, acc)
        cl.login()
        ids = [
            id for id in cl.fetch_message_ids()
            if not message.exists(conn, acc, id)
        ]
        for msg in cl.fetch_messages(ids):
            print('%s: %s at %s' % (msg.sender.fullname, msg.subject, msg.date))
            msg.save(conn)
