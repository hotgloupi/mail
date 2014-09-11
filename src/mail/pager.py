import sys
import subprocess

def setup():
    return subprocess.Popen(['less'], stdin = sys.stdout)
