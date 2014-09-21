import html.parser
import fabulous

from .token import Token
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
        'em': make_color_token(f.start_italic(), f.end_italic()),
        'a': Link,
        'b': make_color_token(f.start_bold(), f.end_bold()),
        'strong': make_color_token(f.start_bold(), f.end_bold()),
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

    def start_nobr(self): pass
    data_nobr = _addstr
    def end_nobr(self): pass

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
    data_em = _addstr
    data_strong = _addstr

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

def parse(data):
    parser = HTMLParser()
    parser.feed(data)
    return parser.sanitized_lines()

