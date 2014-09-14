import argparse
import itertools
import html2text
import mistune
import colorama
from termcolor import colored
import blessings
import textwrap

from mail import message, db, account, object

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-show')
    parser.add_argument(
        'object',
        help = 'Object to show',
        nargs = '+',
    )
    return parser.parse_args(args)


class TerminalRenderer(mistune.Renderer):
    def __init__(self):
        colorama.init()
        self.start = 0
        self.indent = 0
        super().__init__()
        self.term = blessings.Terminal(force_styling = True)

    def link(self, link, title, content):
        res = title and title + ": " or ''
        res += colored(content, 'blue')
        return res

    def paragraph(self, txt):
        res = []
        lines = textwrap.wrap(txt, width = 79)
        for line in lines[:-1]:
            words = line.split()
            spaces = (len(words) - 1) * [' ']
            words_length = sum(len(w) for w in words)
            spaces_left = (80 - len(line))
            word_weights = [
                (len(word), pos) for pos, word in enumerate(words[1:])
            ]
            while spaces_left and word_weights:
                for w, i in reversed(sorted(word_weights)):
                    if not spaces_left: break
                    spaces[i] += ' '
                    spaces_left -= 1
            parts = map(lambda e: ''.join(e), itertools.zip_longest(spaces, words[1:]))
            res.append(words[0] + ''.join(parts))
        if lines:
            res.append(lines[-1])
        return '\n'.join(res) + '\n'

    def list(self, body, ordered = True):
        self.indent = 2
        self.start = 0
        return body + '\n' + '-' * 72 + '\n'
    def list_item(self, txt):
        self.start += 1
        return (
            " " * self.indent + str(self.start) + '. ' + txt + '\n'
        )

    def emphasis(self, txt):
        return self.term.italic + txt + self.term.normal

    def block_quote(self, text):
        return text

def print_html(html, markdown):
    print(markdown.render(html2text.html2text(html)))


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

        lines = textwrap.wrap(paragraph, width = 79)
        for line in lines[:-1]:
            words = line.split()
            spaces = (len(words) - 1) * [' ']
            words_length = sum(len(w) for w in words)
            spaces_left = (80 - len(line))
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


def show_mail(curs, mail, markdown):
    for line in [
        colorama.Style.BRIGHT + "  From: " +  str(mail.sender),
        "  To: " + ' '.join(map(str, mail.recipients)),
        "  At: " + str(mail.date),
        "  Subject: " + colored(mail.pretty_subject, 'red', attrs = ['bold']),
    ]:
        print(line)
    print()
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
        for html in html_parts: print_html(html, markdown)
    elif text_parts:
        for text in text_parts: print_text(text)
    else:
        print(" --- empty message ---")

    curs.execute(
        "SELECT content_type, headers FROM binary_content "\
        "WHERE mail_id = ?",
        (mail.id, )
    )

    for row in curs.fetchall():
        print("CONTENT:", row[0])
    print('-' * 79)




def run(args):
    conn = db.conn()
    curs = conn.cursor()
    markdown = mistune.Markdown(renderer = TerminalRenderer())
    for acc in account.all():
        print("Account:", account)
        for o in args.object:
            if o.startswith('m'):
                mail = message.fetch_one(conn, account_ = acc, id = object.get_id(o))
                show_mail(curs, mail, markdown)

