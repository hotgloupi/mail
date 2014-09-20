import os
import sys
import subprocess
import copy
import string

class Pager:

    def __init__(self, commands = None):
        self.commands = commands
        self.bindings = {}
        i = 0
        for k in self.commands.keys():
            c = string.ascii_letters[i]
            i += 1
            self.bindings[c] = k

    def __enter__(self):
        env = copy.copy(os.environ)
        if self.commands:
            with open("/tmp/lol", 'w') as f:
                p = lambda *args: print(*args, file = f)
                p("#command")
                for c, k in self.bindings.items():
                    p("%s quit %s\\n" % (k, c))
            subprocess.call(['lesskey', '-o', '/tmp/out', '/tmp/lol'])
            env['LESSKEY'] = '/tmp/out'
        env['LESSCHARSET'] = 'utf-8'
        env['LESSUTFBINFMT'] = '*r?' # Normal style for decode errors

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
        r = self.process.returncode
        if r:
            if chr(r) in self.bindings:
                cmd = self.commands[self.bindings[chr(r)]]
                if isinstance(cmd, str):
                    cmd = cmd.split()
                subprocess.call(cmd)

    def print(self, *args):
        #print((' '.join(map(str, args))))
        self.process.stdin.write((' '.join(map(str, args)) + '\n').encode('utf8'))

