from mail import db, account, client, message, object

"""\
Fetch mails or other objects.
"""

arguments = [
    dict (
        flags = 'kind',
        help = 'Stuff to fetch (m[ail], f[lags], b[ox]) or an object',
        nargs = '*',
    ),
]

def fetch_mail(conn, client, kind):
    curs = conn.cursor()
    if object.is_object(kind):
        curs.execute(
            "SELECT remote_id FROM mail WHERE id = ?",
            (object.get_id(kind), )
        )
        res = curs.fetchone()
        if not res:
            raise Exception("Invalid object '%s'" % kind)
        ids = [res[0]]
        should_save = False
    else:
        ids = [
            id for id in client.fetch_message_ids()
            if not message.exists(conn, client.account, remote_id = id)
        ]
        should_save = True
    if not ids:
        print("Everything up-to-date.")
    for idx, msg in enumerate(client.fetch_messages(ids)):
        if should_save:
            msg.save(conn)
        print('[%d/%4d] %s %s: %s at %s' % (
            idx + 1, len(ids),
            msg.uid,
            msg.sender and msg.sender.fullname or "Unknown",
            msg.pretty_subject, msg.date
        ))

def run(args):
    conn = db.conn()
    all = account.all(conn.cursor())
    if not all:
        print('You must add accounts first')
        return 1

    if not args.kind:
        args.kind = ['mail']
    for acc in all:
        cl = client.make(conn, acc)
        cl.login()
        for kind in args.kind:
            if kind.lower().startswith('m'): # mail
                fetch_mail(conn, cl, kind)
            elif kind.lower().startswith('b'): # box
                print("Mailboxes:")
                for m in cl.mailboxes():
                    m.synchronize(conn)
                    print('\t-', m)
            else:
                print("Invalid kind: '%s'" % kind)
                return 1
