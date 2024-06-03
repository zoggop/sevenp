from sys import argv, stdin, stdout
from os import get_terminal_size
from pathlib import Path
from py7zr import SevenZipFile
from pynput import keyboard
from fuzzyfinder import fuzzyfinder
from math import floor

archiveFP = Path(argv[1]).expanduser()
strungOutput = ''

def textsContain(inp, texts):
	# outs = []
	# for text in texts:
	# 	if inp in text:
	# 		outs.append(text)
	# return outs
	return list(fuzzyfinder(inp, texts))

def termColsLines():
	size = get_terminal_size()
	return size.columns, size.lines

def printListInColumns(theList, cols, lines):
	longest = 0
	for i in range(len(theList)):
		s = theList[i]
		slen = len(s)
		if slen > longest:
			longest = slen
	columnWidth = longest + 4
	columns = floor(cols / columnWidth)
	cells = columns * lines
	emptyCell = "".ljust(columnWidth)
	if columns == 0:
		return
	c = 0
	r = 0
	for i in range(cells):
		ni = (c * lines) + r
		if ni == 0:
			marker = '•'
		else:
			marker = ' '
		if ni < len(theList):
			s = theList[ni]
		else:
			s = ''
		stdout.write("{} {}".format(marker, s).ljust(columnWidth))
		c += 1
		if c == columns:
			c = 0
			r += 1
			stdout.write("\n")
	for i in range(lines):
		stdout.write("\033[F")

def clearScreen():
	cols, lines = termColsLines()
	for i in range(lines):
		stdout.write("\033[F")
	for i in range(lines):
		stdout.write(''.ljust(cols))
		stdout.write("\n")

def typeStrungOutput():
	global strungOutput
	kbControl = keyboard.Controller()
	kbControl.type(strungOutput)
	strungOutput = ''

def on_release(key):
	if key == keyboard.Key.esc:
		return False  # stop listener
	try:
		k = key.char  # single-char keys
	except:
		k = key.name  # other keys
	if k == 'home':  # keys of interest
		typeStrungOutput()
		return False  # stop listener; remove this if want more keys

def stringOutput(pw):
	global strungOutput
	strungOutput = pw
	listener = keyboard.Listener(on_release=on_release)
	listener.start()  # start to listen on a separate thread
	listener.join()  # remove if main thread is polling self.keys

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

print(chr(27) + "[2J")

getch = _Getch()

archivePassword = None
archive7z = None
ch = None
s = ''
newFilename = ''
matches = []
while 1 == 1:
	chb = getch()
	try:
		ch = chb.decode("utf-8")
	except:
		ch = None
	cols, lines = termColsLines()
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
					stringOutput(result)
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
			stdout.write(''.ljust(cols)) # clear the password from the terminal
			stdout.write("\n")
			s = newFilename
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
	elif ch:
		s = s + ch
	if archive7z:
		stdout.write(s.ljust(cols))
		stdout.write("\n")
	else:
		mask = ''.ljust(len(s), '•')
		stdout.write(mask.ljust(cols))
		stdout.write("\n")
	if newFilename == '' and archive7z:
		matches = textsContain(s, filenames)
		stdout.write("\n")
		printListInColumns(matches, cols, lines-3)
		stdout.write("\033[F")
		stdout.write("\033[F")
	else:
		stdout.write("\033[F")