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
        for id in cl.fetch_message_ids():
            msg = cl.fetch_message(id)
            if msg is not None:
                print("Saving", msg.remote_id)
                msg.save(conn)
