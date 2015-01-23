import curses
from consts import STACKDEPTH

# module globals defined for each of the windows: statusw, stackw, commandsw
# (two other windows I'm not currently using them will presumably join these
# eventually)

def changeStatusChar(c):
    """Place the indicated character /c/ in the status bracket."""
    statusw.addstr(0,1,c, curses.color_pair(1))
    statusw.refresh()

def changeStatusMsg(msg):
    statusw.addstr(0, 15, ' ' * (80 - 15), curses.color_pair(1))
    statusw.addstr(0, 15, msg, curses.color_pair(1))
    statusw.refresh()

def redrawStackWin(ss):
    stackw.clear()
    stackw.border()
    stackw.addstr(0, 9, "Stack")
    for i in range(len(ss.s)):
        stackw.addstr(1 + i, 1, ss.s[i].entry)

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

def populateCommandsWindow(mode='normal', opts={}):
    def addCommand(char, descr, yposn, xposn):
        commandsw.addstr(yposn, xposn, char, curses.color_pair(2))
        commandsw.addstr(yposn, xposn + 1 + len(char), descr)

    commandsw.clear()
    commandsw.border()
    commandsw.addstr(0, 8, "Commands")

    if mode == 'normal':
        CENTERFACTOR = 1
        addCommand("+ - * / ^ %", "", 1, 5 + CENTERFACTOR)
        addCommand("c", "clear stack", 2, 1 + CENTERFACTOR)
        addCommand("d", "duplicate bos", 3, 1 + CENTERFACTOR)
        addCommand("p", "pop off bos", 4, 1 + CENTERFACTOR)
        addCommand("r", "roll off tos", 5, 1 + CENTERFACTOR)
        addCommand("x", "exchange bos, tos", 6, 1 + CENTERFACTOR)
        addCommand("u", "undo (", 7, 1 + CENTERFACTOR)
        addCommand("^r", "redo)", 7, 9 + CENTERFACTOR)
        addCommand("y", "yank bos to cboard", 8, 1 + CENTERFACTOR)
        addCommand("s", "square root", 9, 1 + CENTERFACTOR)
        addCommand("t", "trig functions", 10, 1 + CENTERFACTOR)
        addCommand("l", "log functions", 11, 1 + CENTERFACTOR)
        addCommand("i", "insert constant", 12, 1 + CENTERFACTOR)
        addCommand("q", "quit", 13, 1 + CENTERFACTOR)

    elif mode == 'trig':
        CENTERFACTOR = 1
        commandsw.addstr(1, 6, "(trig mode)")
        commandsw.addstr(2, 6, " [%s] " % opts['mode'] )
        addCommand("s", "sine", 4, 1 + CENTERFACTOR)
        addCommand("c", "cosine", 5, 1 + CENTERFACTOR)
        addCommand("t", "tangent", 6, 1 + CENTERFACTOR)
        addCommand("i", "arc sin", 7, 1 + CENTERFACTOR)
        addCommand("o", "arc cos", 8, 1 + CENTERFACTOR)
        addCommand("a", "arc tan", 9, 1 + CENTERFACTOR)
        addCommand("d", "degree mode", 10, 1 + CENTERFACTOR)
        addCommand("r", "radian mode", 11, 1 + CENTERFACTOR)
        addCommand("q", "cancel", 12, 1 + CENTERFACTOR)

    elif mode == 'log':
        CENTERFACTOR = 1
        commandsw.addstr(1, 7, "(log mode)")
        addCommand("l", "log x", 3, 1 + CENTERFACTOR)
        addCommand("1", "10^x", 4, 1 + CENTERFACTOR)
        addCommand("e", "ln x", 5, 1 + CENTERFACTOR)
        addCommand("n", "e^x", 6, 1 + CENTERFACTOR)
        addCommand("q", "cancel", 7, 1 + CENTERFACTOR)

    elif mode == 'cst':
        CENTERFACTOR = 1
        commandsw.addstr(1, 4, "(constant mode)")
        addCommand("p", "pi", 3, 1 + CENTERFACTOR)
        addCommand("e", "e", 4, 1 + CENTERFACTOR)
        addCommand("q", "cancel", 5, 1 + CENTERFACTOR)

    else:
        assert False, "Invalid mode used for populateCommandsWindow()"

    commandsw.refresh()

def setup(stdscr):
    maxy, maxx = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

    global statusw, stackw, commandsw

    statusw = curses.newwin(1, maxx, 0, 0)
    #statusw.addstr(0, 0, (' ' * (maxx - 1)), curses.color_pair(1))
    #DEBUG, to see where 80 cols is:
    statusw.addstr(0, 0, (' ' * 80), curses.color_pair(1))
    statusw.addstr(0, 0, "[ ] ic 0.0.1 |", curses.color_pair(1))
    statusw.move(0, 1)

    stackw = curses.newwin(3 + STACKDEPTH, 24, 1, 0)
    stackw.border()
    stackw.addstr(0, 9, "Stack")

    historyw = curses.newwin(3 + STACKDEPTH, 32, 1, 24)
    historyw.border()
    historyw.addstr(0, 13, "History")

    commandsw = curses.newwin(3 + STACKDEPTH, 24, 1, 56)
    populateCommandsWindow()

    #registers = curses.newwin(maxy - (3 + STACKDEPTH), maxx, 4 + STACKDEPTH, 0)
    registersw = curses.newwin(maxy - 1 - (3 + STACKDEPTH), 80, 4 + STACKDEPTH, 0)
    registersw.border()
    registersw.addstr(0, 36, "Registers")

    stackw.refresh()
    statusw.refresh()
    historyw.refresh()
    commandsw.refresh()
    registersw.refresh()
