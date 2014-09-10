import argparse
import sys

from . import commands

def main():
    prog = sys.argv[0]
    args = sys.argv[1:]
    if not args:
        print("usage: {prog} <command> [args...]".format(**locals()))
        return 1
    command = args[0]
    args = args[1:]
    if command not in commands.all:
        print("Unknown command", command)
        return 1

    command = commands.all[command]
    return command.run(command.parse_args(args))
