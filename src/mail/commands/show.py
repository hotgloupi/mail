import argparse
import itertools
import textwrap
import fabulous
from fabulous import image
import fabulous.color
from io import BytesIO

from mail import message, db, account, object, external, pager, text

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-show')
    parser.add_argument(
        'object',
        help = 'Object to show',
        nargs = '+',
    )
    return parser.parse_args(args)


def conservative_split(s):
    res = []
    idx = 0
    while idx <= len(s):
        el = ''
        while idx < len(s) and s[idx] != ' ':
            el += s[idx]
            idx += 1
        res.append(el)
        idx += 1
    return res

def wrap(line, width = 79):
    lines = []
    current_line = []
    current_len = 0
    for part in line:
        if isinstance(part, text.Token):
            current_line.append(part)
            continue
        current_part = ''
        start = True
        for el in conservative_split(part):
            if not start and len(el) + 1 + current_len <= width:
                current_part += ' ' + el
                current_len += len(el) + 1
            elif start:
                current_part += el
                current_len += len(el)
                start = False
            else:
                current_line.append(current_part)
                lines.append(current_line)
                current_part = el
                current_line = []
                current_len = len(el)
        current_line.append(current_part)
    lines.append(current_line)

    #print("LINES:", lines)
    res = []
    for parts in lines:
        cur = []
        for part in parts:
            if isinstance(part, text.Token):
                cur.append(part)
            else:
                for idx, el in enumerate(conservative_split(part)):
                    if idx:
                        cur.append(' ')
                    cur.append(el)
        res.append(cur)
    #print("LINE", line, "->", res)
    return res

def paragraph(p, width = 79):
    if not p: return []
    lines = wrap(p, width)
    res = []
    for line in lines[:-1]:
        words = {}
        spaces = {}
        words_len = 0
        spaces_len = 0
        for idx, word in enumerate(line):
            if isinstance(word, text.Token):
                pass
            elif word == ' ':
                spaces[idx] = ' '
                spaces_len += 1
            else:
                words[idx] = word
                words_len += len(word)
        spaces_left = width - words_len - spaces_len
        def prev_word(line, idx):
            for el in line[:idx]:
                if el != ' ' and not isinstance(el, text.Token):
                    return el
        def next_word(line, idx):
            for el in line[idx + 1:]:
                if el != ' ' and not isinstance(el, text.Token):
                    return el
        if spaces_left > 0:
            words_weight = {}
            for idx in spaces.keys():
                words_weight[idx] = len(next_word(line, idx) or '') + len(prev_word(line, idx) or '')

            while spaces_left > 0 and words_weight:
                for weight, i in reversed(sorted((v, k) for k, v in words_weight.items())):
                    if not spaces_left: break
                    spaces[i] += ' '
                    spaces_left -= 1
        cur = []
        for idx, el in enumerate(line):
            cur.append(spaces.get(idx, words.get(idx, el)))
        res.append(cur)
    if lines:
        res.append(lines[-1])

    return res #'    ' + ('\n' + '    ').join(res)

def print_html(data, pager):
    for p in text.parse_html(data):
        if not p:
            pager.print()
        for line in paragraph(p):
            pager.print(''.join(map(str, line)))

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
        for line in [
            "  From: " +  str(mail.sender),
            "  To: " + ' '.join(map(str, mail.recipients)),
            "  At: " + str(mail.date),
            "  Subject: " + mail.pretty_subject,
        ]:
            less.print(line)
        less.print()
        curs.execute(
            "SELECT content_type, payload FROM text_content "\
            "WHERE mail_id = ?",
            (mail.id, )
        )

        html_parts = []
        text_parts = []
        other_parts = []

        for row in curs.fetchall():
            if row[0] == 'text/html':
                html_parts.append(row[1])
            elif row[0] == 'text/plain':
                text_parts.append(row[1])
            else:
                other_parts.append((row[0], row[1]))

        if html_parts:
            for html in html_parts: print_html(html, less)
        elif text_parts:
            for text in text_parts: print_text(text, less)
        else:
            less.print(" --- empty message ---")

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
        print("Account:", account)
        for o in args.object:
            if o.startswith('m'):
                mail = message.fetch_one(conn, account_ = acc, id = object.get_id(o))
                show_mail(curs, mail)

