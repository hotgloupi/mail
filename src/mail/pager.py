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
                for k, cmd in self.commands.items():
                    p("%s shell %s\\nquit\\n" % (k, cmd))
            subprocess.call(['lesskey', '-o', '/tmp/out', '/tmp/lol'])
            env['LESSKEY'] = '/tmp/out'
        env['LESSCHARSET'] = 'utf-8'
        env['LESSUTFBINFMT'] = '*r?' # Normal style

        self.process = subprocess.Popen(
            ['less', '-r'], # -r is used for multiline ansi code effect
            stdin = subprocess.PIPE,
            env = env
        )
        return self

    def __exit__(self, *args):
        self.process.stdin.close()
        while self.process.returncode is None:
            self.process.poll()

    def print(self, *args):
        #print((' '.join(map(str, args))))
        self.process.stdin.write((' '.join(map(str, args)) + '\n').encode('utf8'))

