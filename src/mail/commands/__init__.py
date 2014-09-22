import argparse
import copy
import importlib
import pathlib
import sys
import traceback

class Command:
    def __init__(self, name, mod):
        self.name = name
        self.mod = mod

    @property
    def doc(self):
        return self.mod.__doc__ or ''

    @property
    def short_doc(self):
        return self.doc.strip().split('\n')[0]

    @property
    def parser(self):
        parser = argparse.ArgumentParser(
            prog = 'mail-%s' % self.name
        )
        for arg in self.mod.arguments:
            kw = copy.copy(arg)
            flags = kw.pop('flags')
            if isinstance(flags, str):
                flags = (flags, )
            parser.add_argument(*flags, **kw)
        return parser

    def parse_args(self, args):
        if hasattr(self.mod, 'parse_args'):
            return self.mod.parse_args(args)
        return self.parser.parse_args(args)

    def run(self, args):
        return self.mod.run(self.parse_args(args))

all = {}
this_file = pathlib.Path(__file__)
for el in this_file.parent.iterdir():
    if str(el).endswith('.py') and not str(el.name).startswith('__'):
        name = el.name[:-3]
        try:
            mod = importlib.import_module("mail.commands." + name)
            all[name] = Command(name, mod)
        except Exception as e:
            traceback.print_exc()
            print("Ignoring command '%s':" % name, e, file = sys.stderr)
