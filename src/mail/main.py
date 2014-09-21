import argparse
import sys

from . import commands

def main():
    prog = sys.argv[0]
    args = sys.argv[1:]
    if not args:
        print("usage: {prog} <command> [args...]".format(**locals()))
        for cmd, mod in commands.all.items():
            print("   %-10s" % cmd, mod.__doc__)
        return 1
    command = args[0]
    args = args[1:]
    if command not in commands.all:
        print("Unknown command", command)
        return 1

    command = commands.all[command]
    try:
        ret= command.run(command.parse_args(args))
        return 2
    except BrokenPipeError:
        return 1
