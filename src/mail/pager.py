import os
import sys
import subprocess
import copy

class Pager:

    def __init__(self, commands = None):
        self.commands = commands

    def __enter__(self):
        env = copy.copy(os.environ)
        if self.commands:
            with open("/tmp/lol", 'w') as f:
                p = lambda *args: print(*args, file = f)
                p("#command")
                p("r shell echo lol\\n")
            subprocess.call(['lesskey', '-o', '/tmp/out', '/tmp/lol'])
            env['LESSKEY'] = '/tmp/out'

        self.process = subprocess.Popen(
            ['less'],
            stdin = subprocess.PIPE,
            env = env
        )
        return self

    def __exit__(self, *args):
        self.process.stdin.close()
        while self.process.returncode is None:
            self.process.poll()

    def print(self, *args):
        self.process.stdin.write(' '.join(map(str, args)).encode('utf8') + b'\n')

