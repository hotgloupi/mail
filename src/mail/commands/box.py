import argparse
import mail.db
import mail.account
import mail.box

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-box')
    return parser.parse_args(args)

def run(args):
    cursor = mail.db.conn().cursor()
    for account in mail.account.all(cursor):
        print("Mailboxes for", account.email, '(%s)' % account.type)
        cursor.execute(
            """
            SELECT id, name, (SELECT count(*) FROM mail WHERE mail.mailbox_id = mailbox.id) FROM mailbox;
            """
        )
        for _, name, count in cursor.fetchall():
            print("\t-", name, '(%s)' % count)
        #for box in mail.box.all(account, cursor):
        #    print('\t-', box)
