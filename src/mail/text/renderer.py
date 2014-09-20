
from . import Token

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

def render(lines, mode = 'terminal', width = 80):
    res = []
    for line in lines:
        if not line:
            res.append('')
        if mode == 'terminal':
            for wrapped_line in paragraph(line, width = width - 1):
                res.append(''.join(map(str, wrapped_line)))
        elif mode == 'text':
            for wrapped_line in paragraph(line,  width = width - 1):
                res.append(
                    ''.join(map(str, (el for el in wrapped_line if not isinstance(el, Token))))
                )
        else:
            raise Exception("Unkown mode '%s'" % mode)
    return res
