from datetime import datetime
from sys import argv, stdin, stdout
from os import get_terminal_size
from pathlib import Path
from pynput import keyboard
from fuzzyfinder import fuzzyfinder
from math import floor

archiveFP = Path(argv[1]).expanduser()
strungOutput = ''

ANSI_END = '\033[0m'

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
	bg, fg = 45, 97
	if matchCopied:
		bg, fg = 102, 30
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
	offset = 0
	if selectedMatch >= cells:
		offset = floor(selectedMatch / cells) * cells
	# print(selectedMatch, cells, offset)
	c = 0
	r = 0
	line = ''
	llen = len(names)
	for i in range(cells):
		ni = (c * lines) + r + offset
		if ni < llen:
			s = names[ni]
		elif showDate and c == 1 and r < llen:
			s = dbn[names[r]].astimezone().strftime("%d/%m/%Y %H:%M:%S")
		else:
			s = ''
		if (ni == selectedMatch and llen > 0) or (showDate and c == 1 and r == selectedMatch):
			whitespace = ''.ljust(columnWidth - len(s))
			if showDate and c == 0:
				end = ''
			else:
				end = ANSI_END
			line += "\033[{};{}m{}{}{}".format(bg, fg, s, end, whitespace)
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
	if strungOutput == '':
		return
	kbControl = keyboard.Controller()
	kbControl.type(strungOutput)
	strungOutput = ''

def on_release(key):
	try:
		k = key.char  # single-char keys
	except:
		k = key.name  # other keys
	if k == 'shift' or k == 'shift_r':  # keys of interest
		typeStrungOutput()

def stringOutput(pw):
	global strungOutput
	strungOutput = pw

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

listener = keyboard.Listener(
	on_release=on_release)
listener.start()

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
confirmedNewFile = False
prevDT = datetime.now()
while 1:
	prevChb = chb
	if not confirmedNewFile and (datetime.now() - prevDT).total_seconds() > 60:
		# exit if it's been a minute, for security
		clearScreen()
		exit()
	prevDT = datetime.now()
	chb = getch()
	try:
		ch = chb.decode("utf-8")
	except:
		ch = None
	cols, lines = termColsLines()
	linesForFiles = lines - 4
	spaceLine = ''.ljust(cols)
	if ch == '\n' or ch == '\r':
		if not filenames:
			from py7zr import SevenZipFile
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
					stringOutput(result)
					matchCopied = True
				archive7z.close()
		elif confirmedNewFile:
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
			confirmedNewFile = False
		else:
			stringOutput(s)
			confirmedNewFile = True
	elif ch == 'P' and prevChb == b'\xe0': # down arrow
		if len(matches) > 1:
			selectedMatch = min(len(matches)-1, selectedMatch + 1)
			matchCopied = False
	elif ch == 'H' and prevChb == b'\xe0': # up arrow
		if len(matches) > 1:
			selectedMatch = max(0, selectedMatch - 1)
			matchCopied = False
	elif ch == 'K' and prevChb == b'\xe0': # left arrow
		if len(matches) > linesForFiles:
			if selectedMatch - linesForFiles >= 0:
				selectedMatch -= linesForFiles
				matchCopied = False
	elif ch == 'M' and prevChb == b'\xe0': # right arrow
		if len(matches) > linesForFiles:
			if selectedMatch + linesForFiles < len(matches):
				selectedMatch += linesForFiles
				matchCopied = False
	elif ch == 'Q' and prevChb == b'\xe0': # page down
		if len(matches) - 1 > displayedMatches + selectedMatch:
			selectedMatch += displayedMatches
			matchCopied = False
		elif len(matches) - 1 > selectedMatch:
			selectedMatch = len(matches) - 1
	elif ch == 'I' and prevChb == b'\xe0': # page up
		if selectedMatch > 0:
			selectedMatch = max(0, selectedMatch - displayedMatches)
			matchCopied = False
	elif ch == '/' and filenames and newFilename == '':
		newFilename = s
		s = ''
		matchCopied = False
	elif ch == '\033':
		if newFilename == '':
			clearScreen()
			exit()
		else:
			s = newFilename
			newFilename = ''
			matchCopied = False
	elif ch == '\b':
		s = s[:-1]
		selectedMatch = 0
		matchCopied = False
		confirmedNewFile = False
	elif ch:
		s += ch
		selectedMatch = 0
		matchCopied = False
		confirmedNewFile = False
	# draw the terminal screen
	stdout.write('\r')
	if filenames:
		if newFilename and confirmedNewFile:
			stdout.write("\033[102;30m{}{}".format(s, ANSI_END).ljust(cols))
		else:
			stdout.write(s.ljust(cols))
		stdout.write("\n\n")
	else:
		mask = ''.ljust(len(s), '•')
		stdout.write(mask.ljust(cols))
	if newFilename == '' and filenames:
		matches = textsContain(s, filenames)
		displayedMatches = printFilesInColumns(matches, dbn, cols, linesForFiles, selectedMatch, matchCopied)
	elif filenames:
		digits = sum(c.isdigit() for c in s)
		uppers = sum(c.isupper() for c in s)
		specials = len(s) - sum(c.isalnum() for c in s)
		stdout.write("{} characters, {} numbers, {} upper case, {} specials".format(len(s), digits, uppers, specials).ljust(cols))
		for i in range(linesForFiles - 1):
			stdout.write(spaceLine)
			stdout.write('\n')
	if filenames:
		stdout.write('\n')
		statusString = ''
		if newFilename == '':
			if strungOutput == '':
				statusString = 'ENTER: Buffer selected.'
			else:
				statusString = 'SHIFT: Output buffer. ENTER: Buffer selected.'
			if len(s) > 0:
				statusString += ' /: New file.'
			statusString += ' ESC: Exit.'
		elif confirmedNewFile:
			statusString = 'SHIFT: Output buffer. ENTER: Write input to file. ESC: Cancel.'
		else:
			statusString = 'ENTER: Buffer input. ESC: Cancel.'
		stdout.write(statusString.ljust(cols))
		for i in range(lines):
			stdout.write("\033[F")
	cursorString = '\r'
	for i in range(len(s)):
		cursorString += '\033[C'
	stdout.write(cursorString)