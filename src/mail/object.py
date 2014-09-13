

kinds = {
    'm': 'mail',
    'b': 'box',
}

to_kinds = {v: k for k, v in kinds.items()}

def is_object(value):
    if isinstance(value, str):
        if len(value) == 9:
            return value[0] in kinds
    return False

def get_id(value):
    assert is_object(value)
    return int(value[1:], base = 16)

def get_kind(value):
    return self.kinds[value[0]]

def to_id(kind, id):
    res = "%s%08x" % (to_kinds[kind], id)
    assert len(res) == 9
    return res
