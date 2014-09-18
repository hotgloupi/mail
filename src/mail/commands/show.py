import argparse
import itertools
import html2text
import mistune
import colorama
import blessings
import textwrap
import fabulous
from fabulous import image
import fabulous.color
from io import BytesIO

from mail import message, db, account, object, external

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
        self.old_text = False
        self.is_image = False

    def link(self, link, title, content):
        res = title and title + ": " or ''
        return str(res + fabulous.color.blue(content))

    def paragraph(self, txt):
        if self.is_image:
            self.is_image = False
            return txt

        if not txt: return ''
        res = []
        lines = textwrap.wrap(txt, width = 71)
        for line in lines[:-1]:
            words = line.split()
            spaces = (len(words) - 1) * [' ']
            words_length = sum(len(w) for w in words)
            spaces_left = (72 - len(line))
            word_weights = [
                (len(word), pos) for pos, word in enumerate(words[1:])
            ]
            if spaces_left < words_length / 2:
                while spaces_left and word_weights:
                    for w, i in reversed(sorted(word_weights)):
                        if not spaces_left: break
                        spaces[i] += ' '
                        spaces_left -= 1
            parts = map(lambda e: ''.join(e), itertools.zip_longest(spaces, words[1:]))
            res.append(words[0] + ''.join(parts))
        if lines:
            res.append(lines[-1])
        if res == ['&gt;']:
            self.old_text = True
            return ''

        if self.old_text:
            self.old_text = False
            res = fabulous.color.bg256("#111", '    ')  + ('\n' + str(fabulous.color.bg256("#111", '    '))).join(res) + '\n'
            return  fabulous.color.bg256("#111", '    ') + '\n' + colorama.Back.RESET+ fabulous.color.fg256("#aaa", res)
        res = '    ' + ('\n' + '    ').join(res) + '\n'
        return '\n'+res

    def list(self, body, ordered = True):
        self.indent = 2
        self.start = 0
        return body + '\n' + '-' * 72 + '\n'
    def list_item(self, txt):
        self.start += 1
        return (
            " " * self.indent + str(self.start) + '. ' + txt + '\n'
        )

    def linebreak(self):
        return '\n\n'

    def emphasis(self, txt):
        return self.term.italic + txt + self.term.normal

    def block_quote(self, text):
        self.old_text = True
        self.has_newline = True
        return text

    def autolink(self, link, is_email = False):
        import re
        link = link.replace('\n', '')
        s = re.search('\[(.*)\]', link)
        if s:
            return self.term.blue(s.group(1))
        else:
            return self.term.italic(self.term.blue(link))

    #has_newline = False
    #def text(self, text):
    #    text = text.strip()
    #    if text == '>':
    #        self.old_text = True
    #        self.has_newline = True
    #        return ''
    #    if not text:
    #        self.has_newline = True
    #    if text:
    #        if self.has_newline:
    #            self.has_newline = False
    #    return text

    def tag(self, html):
        return ("LOLOL")

    def image(self, src, title, alt_text):
        try:
            uri = src.replace('\n', '')
            content_type, content = external.get_resource(uri)
            self.is_image = True
            return '\n    ' + '\n    '.join(image.Image(BytesIO(content), width = 72))
        except:
            import traceback
            traceback.print_exc()
            return "[IMAGE %s (%s)]" % (title or alt_text or '', src)

    def double_emphasis(self, text):
        return self.term.bold(text)

import html.parser

class Token:
    def strip(self): return self

class Link(Token):
    pass

class HTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs = True)
        self.stack = []
        self.lines = []
        self.indent = 0

    def handle_starttag(self, tag, attrs):
        self.indent += 1
        attrs = dict(attrs)
        self.stack.append((tag, attrs))
        getattr(self, "start_%s" % tag)()

    def handle_data(self, data):
        data = data.replace('\r\n', '\n').replace('\r', '\n')
        if not self.stack:
            self._newline_if_empty()
            self._addstr(data)
            return
        m = getattr(self, 'data_%s' % self.tag, None)
        if m:
            m(data)
            #print('.'.join(e[0] for e in self.stack), "HANDLE DATA %s:" % self.tag, '>', data, '<')
        else:
            print('.'.join(e[0] for e in self.stack), "IGNORE DATA %s:" % self.tag, data)

    def handle_endtag(self, tag):
        self.indent -= 1
        getattr(self, "end_%s" % tag)()
        self.stack.pop()


    @property
    def tag(self):
        return self.stack[-1][0]

    @property
    def attrs(self):
        return self.stack[-1][1]

    @property
    def line(self):
        return self.lines[-1]

    def _newline(self):
        self.lines.append([])

    def _newline_if_empty(self):
        if not self.lines:
            self.lines.append([])

    def _addstr(self, data):
        data = data.split('\n')
        self.line.append(data[0])
        self.lines.extend([el] for el in data[1:])

    start_div = _newline
    data_div = _addstr
    def end_div(self): pass

    start_br = _newline
    data_br = _addstr
    def end_br(self): pass

    start_p = _newline
    data_p = _addstr
    def end_p(self): pass

    def start_wbr(self): pass
    data_wbr = _addstr
    def end_wbr(self): pass

    def start_span(self): pass
    data_span = _addstr
    def end_span(self): pass

    def start_a(self):
        self.line.append(Link())
    data_a = _addstr
    def end_a(self):pass

    def start_blockquote(self): pass
    def end_blockquote(self): pass

    def start_html(self): pass
    def end_html(self): pass

    def start_head(self): pass
    def end_head(self): pass

    def start_style(self): pass
    def end_style(self): pass

    def start_body(self): pass
    def end_body(self): pass

    def start_hr(self): pass
    def end_hr(self): pass

    def start_b(self): pass
    def end_b(self): pass

    def start_font(self): pass
    def end_font(self): pass

    def start_meta(self): pass
    def end_meta(self): pass

    def start_title(self):pass
    def end_title(self): pass

    def start_table(self): pass
    def end_table(self): pass

    def start_tr(self): pass
    def end_tr(self): pass

    def start_td(self): pass
    def end_td(self): pass

    def start_img(self): pass
    def end_img(self): pass


    def start_strong(self): pass
    def end_strong(self): pass

    def start_tbody(self): pass
    def end_tbody(self): pass

    def sanitized_lines(self):
        lines = []
        for line in self.lines:
            lines.append([el.strip() for el in line if el.strip()])

        res = []
        i = 0
        sz = len(lines)
        # Skip first empty lines
        while i < sz and not lines[i]:
            i += 1
        while i < len(lines):
            res.append(lines[i])
            i += 1
            if not res[-1]:
                while i < sz and not lines[i]:
                    i += 1
        while res and not res[-1]:
            res.pop()
        return res

def paragraph(p, width = 71):
    lines = []
    current_line = []
    current_len = 0
    for el in p:
        if isinstance(p, Token):
            line.append(el)
            continue
        if len(el) + current_len <= width:
            line.append(el)
            current_len += len(el)
        else:
            lines.append(line)
            line = [el]
            current_len = len(el)
    res = []
    for line in lines[:-1]:
        words = (el for el in line if not isinstance(el, Token))
        spaces = (len(words) - 1) * [' ']
        words_length = sum(len(w) for w in words)
        spaces_left = (72 - len(line))
        word_weights = [
            (len(word), pos) for pos, word in enumerate(words[1:])
        ]
        if spaces_left < words_length / 2:
            while spaces_left and word_weights:
                for w, i in reversed(sorted(word_weights)):
                    if not spaces_left: break
                    spaces[i] += ' '
                    spaces_left -= 1
        parts = map(lambda e: ''.join(e), itertools.zip_longest(spaces, words[1:]))
        res.append(words[0] + ''.join(parts))
    if lines:
        res.append(lines[-1])

    return '    ' + ('\n' + '    ').join(res)

def print_html(html, markdown):
    parser = HTMLParser()
    parser.feed(html)
    for line in parser.sanitized_lines():
        print(paragraph(line))
    #print(html.replace('><', '>\n<'))
    #print(markdown.render(html2text.html2text(html)))


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


def show_mail(curs, mail, markdown):
    term = markdown.renderer.term
    for line in [
        term.shadow + "  From: " +  str(mail.sender),
        "  To: " + ' '.join(map(str, mail.recipients)),
        "  At: " + str(mail.date),
        "  Subject: " + mail.pretty_subject + term.normal,
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
        "SELECT content_type, headers, payload FROM binary_content "\
        "WHERE mail_id = ?",
        (mail.id, )
    )

    for row in curs.fetchall():
        content_type = row[0]
        print("CONTENT:", row[0])
        if content_type.startswith('image/'):
            for line in image.Image(BytesIO(row[2])):
                print(line)
            pass
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

