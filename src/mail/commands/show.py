import argparse
import itertools
import textwrap
import fabulous
from fabulous import image
import fabulous.color
from io import BytesIO

from mail import message, db, account, object, external, pager

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-show')
    parser.add_argument(
        'object',
        help = 'Object to show',
        nargs = '+',
    )
    return parser.parse_args(args)

import html.parser

class Token:
    def __init__(self, start, tag, attrs):
        self.start = start
        self.tag = tag
        self.attrs = attrs

class Link(Token):
    def __str__(self):
        if self.start:
            return fabulous.color.fg_start((120,120,220))
        return fabulous.color.fg_end()

class Line(Token):
    def __str__(self):
        if self.start:
            return '-' * 80 + '\n'
        return ''

def make_color_token(start, end):
    class _(Token):
        def __str__(self):
            if self.start: return start
            return end
    return _


class HTMLParser(html.parser.HTMLParser):

    import fabulous.color as f
    token_classes = {
        'i': make_color_token(f.start_italic(), f.end_italic()),
        'a': Link,
        'b': make_color_token(f.start_bold(), f.end_bold()),
        'h1': make_color_token(f.start_bold(), f.end_bold()),
        'h2': make_color_token(f.start_bold(), f.end_bold()),
    }

    def __init__(self):
        super().__init__(convert_charrefs = True)
        self.stack = []
        self.lines = []
        self.indent = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'o:p':
            tag = 'p'
        self.indent += 1
        attrs = dict(attrs)
        self.stack.append((tag, attrs))
        if tag in self.token_classes:
            self.line.append(
                self.token_classes[tag](True, tag, attrs)
            )
        else:
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
            #print('.'.join(e[0] for e in self.stack), "HANDLE DATA %s: '%s'" % (self.tag, data))
        else:
            if data.strip():
                print('.'.join(e[0] for e in self.stack), "IGNORE DATA %s:" % self.tag, data)

    def handle_endtag(self, tag):
        if tag == 'o:p':
            tag = 'p'
        self.indent -= 1
        if tag in self.token_classes:
            self.line.append(
                self.token_classes[tag](False, tag, self.attrs)
            )
        else:
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

    def _append_token(cls):
        def m(self):
            self.line.append(cls())
        return m

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

    data_a = _addstr

    def start_blockquote(self): pass
    def end_blockquote(self): pass

    def start_html(self): pass
    def end_html(self): pass

    def start_head(self): pass
    def end_head(self): pass

    def start_style(self): pass
    def data_style(self, data): pass # Ignore styles
    def end_style(self): pass

    def start_body(self): pass
    def end_body(self): pass

    def start_hr(self):
        self._newline()
        self.line.append(Line(True, 'hr', self.attrs))
    data_hr = _addstr
    def end_hr(self): pass

    data_b = _addstr

    def start_font(self): pass
    data_font = _addstr
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
            lines.append([el for el in line if isinstance(el, Token) or el.strip()])

        res = []
        i = 0
        sz = len(lines)
        def isempty(line):
            for el in line:
                if not isinstance(el, Token) and el.strip():
                    return False
            return True
        # Skip first empty lines
        while i < sz and not lines[i]:
            i += 1
        while i < len(lines):
            res.append(lines[i])
            i += 1
            if isempty(res[-1]):
                while i < sz and isempty(lines[i]):
                    res[-1].extend(el for el in lines[i] if isinstance(el, Token))
                    i += 1
        while res and not res[-1]:
            res.pop()
        return res

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
        if isinstance(part, Token):
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
            if isinstance(part, Token):
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
            if isinstance(word, Token):
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
                if el != ' ' and not isinstance(el, Token):
                    return el
        def next_word(line, idx):
            for el in line[idx + 1:]:
                if el != ' ' and not isinstance(el, Token):
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

def print_html(html, pager):
    parser = HTMLParser()
    parser.feed(html)
    for p in parser.sanitized_lines():
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
    with pager.Pager(commands = 12) as less:
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

