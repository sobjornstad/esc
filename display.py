import curses
from consts import STACKDEPTH, STACKWIDTH, PROGRAM_NAME
from time import sleep #debug

# module globals defined for each of the windows: statusw, stackw, commandsw
# (two other windows I'm not currently using them will presumably join these
# eventually)

def changeStatusChar(c):
    """Place the indicated character /c/ in the status bracket."""
    statusw.addstr(0,1,c, curses.color_pair(1))
    statusw.refresh()

def cursorInStatusBar():
    "Place the cursor in the status bar bracket."
    statusw.move(0, 1)

def changeStatusMsg(msg):
    statusw.addstr(0, 16, ' ' * (80 - 15), curses.color_pair(1))
    statusw.addstr(0, 16, msg, curses.color_pair(1))
    statusw.refresh()

def redrawStackWin(ss):
    stackw.clear()
    stackw.border()
    stackw.addstr(0, 9, "Stack")
    for i in range(len(ss.s)):
        try:
            stackw.addstr(1 + i, 1, ss.s[i].entry)
        except AttributeError:
            print type(ss.s[i])
            print dir(ss.s[i])
            sleep(5)

def defaultStackCursorPos(ss):
    stackw.move(1 + ss.stackPosn, ss.cursorPosn + 1)

def adjustCursorPos(ss):
    defaultStackCursorPos(ss)
    if not ss.editingStack:
        # when not editing a number, cursor goes on *next line*
        stackw.move(2 + ss.stackPosn, ss.cursorPosn + 1)
        changeStatusChar(' ')
    else:
        changeStatusChar('i')

def displayBackspace(ss, ssReturn):
    if ssReturn == 0:
        stackw.addstr(1 + ss.stackPosn, ss.cursorPosn + 1, ' ')
        stackw.move(1 + ss.stackPosn, ss.cursorPosn + 1)
    elif ssReturn == 1:
        stackw.addstr(2 + ss.stackPosn, ss.cursorPosn + 1, ' ')
        stackw.move(2 + ss.stackPosn, ss.cursorPosn + 1)

def getch_stack():
    return stackw.getch()
def putch_stack(c):
    stackw.addstr(c)
def getch_status():
    cursorInStatusBar()
    return statusw.getch()

def addMenuTitle(text, yposn, xposn):
    text = "(%s)" % text
    ctrxpos = (STACKWIDTH - len(text)) / 2 + 1
    addCommand('', text, yposn, ctrxpos)


def addCommand(char, descr, yposn, xposn):
    try:
        commandsw.addstr(yposn, xposn, char, curses.color_pair(2))
        if descr:
            commandsw.addstr(yposn, xposn + 1 + len(char), descr)
    except curses.error:
        pass

def resetCommandsWindow():
    commandsw.clear()
    commandsw.border()
    commandsw.addstr(0, 8, "Commands")

def setup(stdscr):
    maxy, maxx = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

    global statusw, stackw, commandsw

    statusw = curses.newwin(1, maxx, 0, 0)
    #statusw.addstr(0, 0, (' ' * (maxx - 1)), curses.color_pair(1))
    #DEBUG, to see where 80 cols is:
    statusw.addstr(0, 0, (' ' * 80), curses.color_pair(1))
    statusw.addstr(0, 0, "[ ] %s |" % PROGRAM_NAME, curses.color_pair(1))
    statusw.move(0, 1)

    stackw = curses.newwin(3 + STACKDEPTH, 24, 1, 0)
    stackw.border()
    stackw.addstr(0, 9, "Stack")

    historyw = curses.newwin(3 + STACKDEPTH, 32, 1, 24)
    historyw.border()
    historyw.addstr(0, 13, "History")

    commandsw = curses.newwin(3 + STACKDEPTH, 24, 1, 56)
    # will be populated in main() after initializing the FunctionManager

    #registers = curses.newwin(maxy - (3 + STACKDEPTH), maxx, 4 + STACKDEPTH, 0)
    registersw = curses.newwin(maxy - 1 - (3 + STACKDEPTH), 80, 4 + STACKDEPTH, 0)
    registersw.border()
    registersw.addstr(0, 36, "Registers")

    stackw.refresh()
    statusw.refresh()
    historyw.refresh()
    commandsw.refresh()
    registersw.refresh()
