from sys import argv, stdin, stdout
from os import get_terminal_size
from pathlib import Path
from py7zr import SevenZipFile
from pynput import keyboard
from fuzzyfinder import fuzzyfinder
from math import floor
from pyperclip import copy as clipboardCopy

archiveFP = Path(argv[1]).expanduser()
strungOutput = ''

def textsContain(inp, texts):
	return list(fuzzyfinder(inp, texts))

def termColsLines():
	size = get_terminal_size()
	return size.columns, size.lines

def datesByName(infos):
	DbyN = {}
	for info in infos:
		DbyN[info.filename] = info.creationtime
	return DbyN

def printFilesInColumns(names, dbn, cols, lines, selectedMatch, matchCopied):
	bg = 103
	if matchCopied:
		bg = 102
	longest = 0
	showDate = False
	for i in range(len(names)):
		s = names[i]
		slen = len(s)
		if slen > longest:
			longest = slen
	columnWidth = longest + 2
	columns = floor(cols / columnWidth)
	cells = columns * lines
	if columns == 0:
		return
	if len(names) <= lines:
		showDate = True
		columns = 2
		cells = lines * 2
	c = 0
	r = 0
	line = ''
	llen = len(names)
	for i in range(cells):
		ni = (c * lines) + r
		if ni < llen:
			s = names[ni]
		elif showDate and c == 1 and r < llen:
			s = dbn[names[r]].strftime("%d-%m-%Y %H:%M")
		else:
			s = ''
		if (ni == selectedMatch and llen > 0) or (showDate and c == 1 and r == selectedMatch):
			whitespace = ''.ljust(columnWidth - len(s))
			line += "\033[4;30;{}m{}\033[0m{}".format(bg, s, whitespace)
		else:
			line += s.ljust(columnWidth)
		c += 1
		if c == columns:
			c = 0
			r += 1
			stdout.write("{}\n".format(line.ljust(cols)))
			line = ''
	return cells

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
	if k == 'shift':  # keys of interest
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

getch = _Getch()

archivePassword = None
filenames = None
dbn = None
ch = None
chb = None
s = ''
newFilename = ''
matches = []
selectedMatch = 0
prevChb = None
matchCopied = False
displayedMatches = 1
while 1:
	prevChb = chb
	chb = getch()
	try:
		ch = chb.decode("utf-8")
	except:
		ch = None
	cols, lines = termColsLines()
	spaceLine = ''.ljust(cols)
	if ch == '\n' or ch == '\r':
		if not filenames:
			try:
				archive7z = SevenZipFile(archiveFP, mode='r', password=s)
			except:
				archive7z = None
			else:
				filenames = archive7z.getnames()
				dbn = datesByName(archive7z.list())
				archive7z.close()
				archivePassword = s
				print(chr(27) + "[2J")
			finally:
				s = ''
		elif newFilename == '':
			matches = textsContain(s, filenames)
			if len(matches) > 0:
				filename = matches[selectedMatch]
				archive7z = SevenZipFile(archiveFP, mode='r', password=archivePassword)
				for fname, bio in archive7z.read([filename]).items():
					result = bio.read().decode("utf-8").rstrip()
					clipboardCopy(result)
					# stringOutput(result)
					matchCopied = True
				archive7z.close()
		else:
			selectedMatch = 0
			newFilepath = Path('~/' + newFilename).expanduser()
			with open(newFilepath, 'w') as newFile:
				newFile.write(s)
			# make a backup
			from shutil import copyfile
			from datetime import datetime
			dtstring = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
			copyfile(archiveFP, str(archiveFP.parent) + '/' + archiveFP.stem + '-' + dtstring + '.7z')
			archive7z = SevenZipFile(archiveFP, mode='a', password=archivePassword)
			archive7z.set_encrypted_header(True)
			archive7z.write(newFilepath, arcname=newFilename)
			newFilepath.unlink()
			s = newFilename
			newFilename = ''
			archive7z.close()
			archive7z = SevenZipFile(archiveFP, mode='r', password=archivePassword)
			filenames = archive7z.getnames()
			dbn = datesByName(archive7z.list())
			archive7z.close()
	elif ch == 'P' and prevChb == b'\xe0': # down arrow
		if len(matches) > 1:
			selectedMatch = (selectedMatch + 1) % min(len(matches), displayedMatches)
		matchCopied = False
	elif ch == 'H' and prevChb == b'\xe0': # up arrow
		if len(matches) > 1:
			selectedMatch = (selectedMatch - 1) % min(len(matches), displayedMatches)
		matchCopied = False
	elif ch == 'K' and prevChb == b'\xe0': # left arrow
		nothing = 0
	elif ch == 'M' and prevChb == b'\xe0': # right arrow
		nothing = 0
	elif ch == '/' and filenames and newFilename == '':
		newFilename = s
		s = ''
		matchCopied = False
	elif ch == '\033':
		if newFilename == '':
			clearScreen()
			break
		else:
			s = newFilename
			newFilename = ''
			matchCopied = False
	elif ch == '\b':
		s = s[:-1]
		selectedMatch = 0
		matchCopied = False
	elif ch:
		s += ch
		selectedMatch = 0
		matchCopied = False
	# draw the terminal screen
	stdout.write('\r')
	if filenames:
		stdout.write(s.ljust(cols))
		stdout.write("\n\n")
	else:
		mask = ''.ljust(len(s), '•')
		stdout.write(mask.ljust(cols))
	if newFilename == '' and filenames:
		matches = textsContain(s, filenames)
		displayedMatches = printFilesInColumns(matches, dbn, cols, lines-4, selectedMatch, matchCopied)
	elif filenames:
		digits = sum(c.isdigit() for c in s)
		uppers = sum(c.isupper() for c in s)
		specials = len(s) - sum(c.isalnum() for c in s)
		stdout.write("{} characters, {} numbers, {} upper case, {} specials".format(len(s), digits, uppers, specials).ljust(cols))
		for i in range(lines-5):
			stdout.write(spaceLine)
			stdout.write('\n')
	if filenames:
		stdout.write('\n')
		statusString = ''
		if newFilename == '':
			statusString = 'ENTER: Copy selected contents. /: New file with input as filename. ESC: Exit.'
		else:
			statusString = 'ENTER: Write input to new file and add to archive. ESC: Cancel.'
		stdout.write(statusString.ljust(cols))
		for i in range(lines):
			stdout.write("\033[F")
	cursorString = '\r'
	for i in range(len(s)):
		cursorString += '\033[C'
	stdout.write(cursorString)