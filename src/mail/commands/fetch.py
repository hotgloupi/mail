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
        for idx, msg in enumerate(cl.fetch_messages(ids)):
            print('[%d/%4d] %s: %s at %s' % (idx, len(ids), msg.sender and msg.sender.fullname or "Unknown", msg.subject, msg.date))
            msg.save(conn)
