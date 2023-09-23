import sys
import pathlib
import py7zr
from getpass import getpass
import pyperclip

archiveFP = pathlib.Path(sys.argv[1]).expanduser()

def textsContain(inp, texts):
	outs = []
	for text in texts:
		if inp in text:
			outs.append(text)
	return outs

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

archivePassword = getpass('password: ')
archive7z = py7zr.SevenZipFile(archiveFP, mode='r', password=archivePassword)
filenames = archive7z.getnames()

sys.stdout.write('\n')
ch = ''
s = ''
matches = []
while ch != '\033':
	ch = getch().decode("utf-8")
	if ch == '\n' or ch == '\r':
		for i in range(10):
			sys.stdout.write("\n")
		matches = textsContain(s, filenames)
		filename = matches[0]
		print(filename)
		for fname, bio in archive7z.read([filename]).items():
			result = bio.read().decode("utf-8").rstrip()
			pyperclip.copy(result)
		break
	s = s + ch
	matches = textsContain(s, filenames)
	sys.stdout.write("{}\n\n".format(s))
	for m in range(8):
		if m < len(matches):
			match = matches[m]
		else:
			match = ''
		sys.stdout.write("{:40s}\n".format(match))
	for i in range(10):
		sys.stdout.write("\033[F")