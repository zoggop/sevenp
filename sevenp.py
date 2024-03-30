from sys import argv, stdin, stdout
from pathlib import Path
from py7zr import SevenZipFile
from getpass import getpass
import pyperclip

archiveFP = Path(argv[1]).expanduser()

def textsContain(inp, texts):
	outs = []
	for text in texts:
		if inp in text:
			outs.append(text)
	return outs

def clearScreen():
	for i in range(10):
		stdout.write("{:40s}\n".format(''))

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
        fd = stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(stdin.fileno())
            ch = stdin.read(1)
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
archive7z = None
while not archive7z:
	try:
		archive7z = SevenZipFile(archiveFP, mode='r', password=archivePassword)
	except:
		print('incorrect password')
		archivePassword = getpass('password: ')
filenames = archive7z.getnames()

stdout.write('\n')
ch = ''
s = ''
newFilename = ''
matches = []
while 1 == 1:
	ch = getch().decode("utf-8")
	if ch == '\n' or ch == '\r':
		if newFilename == '':
			matches = textsContain(s, filenames)
			if len(matches) > 0:
				clearScreen()
				filename = matches[0]
				print(filename)
				for fname, bio in archive7z.read([filename]).items():
					result = bio.read().decode("utf-8").rstrip()
					pyperclip.copy(result)
				break
			else:
				newFilename = s
				s = ''
		else:
			newFilepath = Path('~/' + newFilename).expanduser()
			with open(newFilepath, 'w') as newFile:
				newFile.write(s)
			archive7z.close()
			# make a backup
			from shutil import copyfile
			from datetime import datetime
			dtstring = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
			copyfile(archiveFP, str(archiveFP.parent) + '/' + archiveFP.stem + '-' + dtstring + '.7z')
			archive7z = SevenZipFile(archiveFP, mode='a', password=archivePassword)
			archive7z.set_encrypted_header(True)
			archive7z.write(newFilepath, arcname=newFilename)
			newFilepath.unlink()
			stdout.write("{:40s}\n".format('')) # clear the password from the terminal
			pyperclip.copy(s)
			break
	elif ch == '\033':
		clearScreen()
		break
	elif ch == '\b':
		s = s[:-1]
	else:
		s = s + ch
	stdout.write("{:40s}\n".format(s))
	if newFilename == '':
		stdout.write("\n")
		matches = textsContain(s, filenames)
		for m in range(8):
			if m < len(matches):
				match = matches[m]
			else:
				match = ''
			stdout.write("{:40s}\n".format(match))
		for i in range(10):
			stdout.write("\033[F")
	else:
		stdout.write("\033[F")

archive7z.close()