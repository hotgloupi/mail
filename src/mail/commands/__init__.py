
import importlib
import pathlib

all = {}
this_file = pathlib.Path(__file__)
for el in this_file.parent.iterdir():
    if str(el).endswith('.py') and not str(el.name).startswith('__'):
        mod = importlib.import_module("mail.commands." + el.name[:-3])
        all[el.name[:-3]] = mod

