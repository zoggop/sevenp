from sys import argv, stdin, stdout
from pathlib import Path
from py7zr import SevenZipFile
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

archivePassword = None
archive7z = None
ch = ''
s = ''
newFilename = ''
matches = []
while 1 == 1:
	ch = getch().decode("utf-8")
	if ch == '\n' or ch == '\r':
		if not archive7z:
			try:
				archive7z = SevenZipFile(archiveFP, mode='r', password=s)
			except:
				archive7z = None
			else:
				filenames = archive7z.getnames()
				archivePassword = s
			finally:
				s = ''
		elif newFilename == '':
			matches = textsContain(s, filenames)
			if len(matches) > 0:
				filename = matches[0]
				for fname, bio in archive7z.read([filename]).items():
					result = bio.read().decode("utf-8").rstrip()
					pyperclip.copy(result)
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
			s = ''
			newFilename = ''
			archive7z.close()
			archive7z = SevenZipFile(archiveFP, mode='r', password=archivePassword)
			filenames = archive7z.getnames()
	elif ch == '/' and archive7z:
		newFilename = s
		s = ''
	elif ch == '\033':
		clearScreen()
		if archive7z:
			archive7z.close()
		break
	elif ch == '\b':
		s = s[:-1]
	else:
		s = s + ch
	if archive7z:
		stdout.write("{:40s}\n".format(s))
	else:
		mask = ''.ljust(len(s), '•')
		stdout.write("{:40s}\n".format(mask))
	if newFilename == '' and archive7z:
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