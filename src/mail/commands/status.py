from mail import db, account, client, message, object
import fabulous.color

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

    curs.execute("SELECT object, action FROM staged")

    staged = dict(
        (object.get_id(row[0]), row[1]) for row in curs.fetchall()
    )

    if staged.items():
        print("Staged for commit:")
        print("  (Use mail reset ... to unstage it again)")
        print()
        for mail_id, action in staged.items():
            msg = message.fetch_one(conn, mail_id)
            print(
                '    ',
                fabulous.color.fg256('#2b2', ' '.join([
                    "%-15s" % (action + ':'), msg.uid, msg.date, msg.pretty_subject
                ]))
            )

    if unread:
        print()
        print("Unread mails:")
        print("  (Use mail read ... to mark it as read)")
        print()
        for mail_id in unread:
            if mail_id in staged:
                continue
            msg = message.fetch_one(conn, mail_id)
            print(
                '    ',
                fabulous.color.fg256('#b22', ' '.join([
                    "%-15s" % 'unread:', msg.uid, msg.date, msg.pretty_subject
                ]))
            )

