
from . import gmail

def make(conn, account, **kw):
    return {
        'gmail': gmail.Client,
    }[account.type](conn, account, **kw)
