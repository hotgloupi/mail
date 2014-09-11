import argparse

from mail import db, account, client, message

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-fetch')
    parser.add_argument(
        'what',
        help = 'What kind of stuff do you want to fetch',
        choices = [
            'mail',
            'flags',
            'box',
            [],
        ],
        nargs = '*',
    )
    return parser.parse_args(args)


def fetch_mail(conn, client):
    ids = [
        id for id in client.fetch_message_ids()
        if not message.exists(conn, client.account, id)
    ]
    if not ids:
        print("Everything up-to-date.")
    for idx, msg in enumerate(client.fetch_messages(ids)):
        print('[%d/%4d] %s: %s at %s' % (
            idx + 1, len(ids),
            msg.sender and msg.sender.fullname or "Unknown",
            msg.subject, msg.date
        ))
        msg.save(conn)

def run(args):
    conn = db.conn()
    all = account.all(conn.cursor())
    if not all:
        print('You must add accounts first')
        return 1

    for acc in all:
        cl = client.make(conn, acc)
        cl.login()
        print(args.what)
        for what in args.what:
            if what == 'mail':
                fetch_mail(conn, cl)
            elif what == 'box':
                print(cl.mailboxes())
