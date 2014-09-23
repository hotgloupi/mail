import fabulous.color

from mail import db, message
from .show import show_mail

__doc__ = """\
Read unseen mails one after another.
"""

arguments = [
    dict(
        flags = ('-a', '--all'),
        help = 'Mark all mail as read',
        action = 'store_true',
    ),
]


def run(args):
    conn = db.conn()
    curs = conn.cursor()
    curs.execute("SELECT mail_id FROM mail_flag WHERE key = 'seen' AND value = 'false'")
    unread = [row[0] for row in curs.fetchall()]

    if args.all:
        print("Mark as read the following mails:")
        # XXX Should really be optimized
        for mail_id in unread:
            msg = message.fetch_one(conn, mail_id)
            print(
                '    ',
                fabulous.color.fg256('#2b2', ' '.join([
                    msg.uid, msg.date, msg.pretty_subject
                ]))
            )
            msg.mark_as_read(conn)
    else:
        for mail_id in unread:
            mail = message.fetch_one(conn, mail_id)
            show_mail(
                curs,
                message.fetch_one(conn, mail_id)
            )
            mail.mark_as_read(conn)
