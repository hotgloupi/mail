import argparse

from mail import db, account, client, message, object

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-fetch')
    return parser.parse_args(args)


def run(args):
    conn = db.conn()
    curs = conn.cursor()
    curs.execute("SELECT mail_id FROM mail_flag WHERE key = 'seen' AND value = 'false'")
    for row in curs.fetchall():
        msg = message.fetch_one(conn, row[0])
        print(msg.uid, msg.pretty_subject)


