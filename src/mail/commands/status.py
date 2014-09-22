from mail import db, account, client, message, object

__doc__ = """\
    Display (un)staged mail actions.
"""

arguments = [
]

def run(args):
    conn = db.conn()
    curs = conn.cursor()
    curs.execute("SELECT mail_id FROM mail_flag WHERE key = 'seen' AND value = 'false'")
    unread = [row[0] for row in curs.fetchall()]

    curs.execute(
        "SELECT object, action FROM staged WHERE object in (%s)" %
            ', '.join("'%s'" % object.to_id('mail', id) for id in unread)
    )

    staged = dict(
        (object.get_id(row[0]), row[1]) for row in curs.fetchall()
    )

    if staged.items():
        print("Staged for commit:")
        for mail_id, action in staged.items():
            print("\t", mail_id, action)

    if unread:
        print("Unread mails")
        for mail_id in unread:
            if mail_id in staged:
                continue
            msg = message.fetch_one(conn, mail_id)
            print("\t", msg.uid, msg.date, msg.pretty_subject)


