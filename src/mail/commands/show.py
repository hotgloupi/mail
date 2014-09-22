import itertools
import textwrap
import fabulous
from fabulous import image
import fabulous.color
from io import BytesIO

from mail import message, db, account, object, external, pager, text

__doc__ = """\
Display a mail.

"""
arguments = [
    {
        'flags': ('object', ),
        'help': 'Object to show',
        'nargs': '+'
    }
]

def print_text(text):
    prev_len = 0
    for paragraph in text.split('\n'):
        if prev_len < 80:
            if len(paragraph) > 79:
                print()
        else:
            print()
        if paragraph.startswith('>'):
            pass

        lines = textwrap.wrap(paragraph, width = 72)
        for line in lines[:-1]:
            words = line.split()
            spaces = (len(words) - 1) * [' ']
            words_length = sum(len(w) for w in words)
            spaces_left = (72 - len(line))
            word_weights = [
                (len(word), pos) for pos, word in enumerate(words[1:])
            ]
            while spaces_left and word_weights:
                for w, i in reversed(sorted(word_weights)):
                    if not spaces_left: break
                    spaces[i] += ' '
                    spaces_left -= 1
            parts = map(lambda e: ''.join(e), itertools.zip_longest(spaces, words[1:]))
            print(words[0] + ''.join(parts))
        if lines:
            print(lines[-1])#, "]--")
        prev_len = len(paragraph)


def show_mail(curs, mail):
    commands = {
        'r': 'mail reply %s' % mail.uid,
        'a': 'mail reply --all %s' % mail.uid,
    }
    with pager.Pager(commands = commands) as less:
        for line in mail.render(curs):
            less.print(line)
        curs.execute(
            "SELECT content_type, headers, payload FROM binary_content "\
            "WHERE mail_id = ?",
            (mail.id, )
        )

        for row in curs.fetchall():
            content_type = row[0]
            less.print("CONTENT:", row[0])
            if content_type.startswith('image/'):
                for line in image.Image(BytesIO(row[2])):
                    less.print(line)
                pass
            less.print('-' * 79)


def run(args):
    conn = db.conn()
    curs = conn.cursor()
    for acc in account.all():
        print("Account:", acc)
        for o in args.object:
            if o.startswith('m'):
                mail = message.fetch_one(conn, account_ = acc, id = object.get_id(o))
                show_mail(curs, mail)

