from curses import wrapper

def main(stdscr):
    # Clear screen
    stdscr.clear()

    # This raises ZeroDivisionError when i == 10.
    for i in range(11):
        stdscr.addstr(i, 0, '{}'.format(i))

    stdscr.refresh()
    stdscr.getkey()

wrapper(main)