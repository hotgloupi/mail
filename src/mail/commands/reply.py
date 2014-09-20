import subprocess
import argparse
import os

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-reply')
    parser.add_argument(
        'mail',
        help = 'Mail to reply to',
        nargs = '+',
    )
    parser.add_argument(
        '--all', '-a',
        help = 'Reply to all'
    )
    return parser.parse_args(args)

from mail import object, message, db

def run(args):
    conn = db.conn()
    for uid in args.mail:
        if not object.is_object(uid):
            print("'%s' is not a valid object" % uid)
            return 1
        if object.get_kind(uid) != 'mail':
            print("'%s' does not refer to a mail" % uid)
        mail = message.fetch_one(conn, object.get_id(uid))
        with open('/tmp/lol', 'w') as f:
            f.write('\n\n')
            f.write("## This line and the lines above won't be included\n")
            f.write("## Just move text that you wish to be included above the previous line\n")
            f.write('\n')
            for line in mail.render(conn.cursor(), mode = 'text', width = 78):
                if line:
                    print('>', line, file = f)
                else:
                    print('>', file = f)
        subprocess.call([os.getenv('EDITOR'), '/tmp/lol'])
