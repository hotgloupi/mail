import argparse

def parse_args(args):
    parser = argparse.ArgumentParser(prog = 'mail-reply')
    parser.add_argument(
        'mail',
        help = 'Mail to reply to',
        nargs = '+',
    )
    return parser.parse_args(args)


def run(args):
    pass
