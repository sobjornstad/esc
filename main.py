#!/usr/bin/env python

#TODO:
# History section.
# Registers.
# Logarithm menu.
# Don't panic if stack width exceeded, or if other invalid input
#   (e.g., entering an 'e' where it can't be scientific notation,
#    multiple decimals, negative by itself)
# A bit more documentation
# Start project commits
# It's sometimes possible to overflow the stack window? It should do sci notation.
# Fix undoing and checkpoints; it fails at many important operations.

import curses
import curses.wrapper
import curses.ascii
from time import sleep
import copy
import math

STACKDEPTH = 12
STACKWIDTH = 20
stackCheckpoints = []
redoCheckpoints = []

class StackItem(object):
    def __init__(self, firstchar=None, floatval=None):
        if firstchar is not None:
            self.isEntered = False
            self.entry = firstchar
            self.value = None
        elif floatval is not None:
            self.isEntered = True
            # don't add a .0 to the fake entry, the user wouldn't have
            self.entry = ftostr(floatval)
            self.value = floatval

    def addChar(self, nextchar):
        assert not self.isEntered, "Number already entered!"
        self.entry += nextchar

    def finishEntry(self):
        self.isEntered = True
        self.value = float(self.entry)

    def getReprStrlen(self):
        """
        Return the number of characters taken to represent the number as a
        string on the stack. Useful for knowing what to overwrite when emptying
        that row of the stack.
        """

        return len(self.entry)

class StackState(object):
    """
    An object containing the current state of the stack: a stack pointer, the
    screen cursor's position across on the current value, the stack itself as a
    list, and whether we are currently editing a number, as well as any mode
    options, which are not strictly part of the stack but are part of the
    program state and should follow it anyway.

    Values may be manipulated directly as convenient. There are also several
    helper methods for convenience.

    Generally, a StackState object should be initialized at the beginning of
    execution and used until the program exits.
    """


    def __init__(self):
        self.clearStack()
        self.trigMode = 'degrees'

    def clearStack(self):
        "Set up an empty stack, or clear the stack."
        self.s = []
        self.stackPosn = -1
        self.cursorPosn = 0
        self.editingStack = False # whether we are editing a number

    def backspace(self):
        """
        Backspace one character in the current item on the stack. Return 0 if a
        character was backspaced, 1 if the whole stack was wiped out, and -1 if
        a stack item was not being edited at all.
        """

        if self.editingStack:
            if self.cursorPosn == 1:
                # remove the stack item in progress
                self.deleteEndOfStack()
                return 1
            self.s[self.stackPosn].entry = self.s[self.stackPosn].entry[0:-1]
            self.cursorPosn -= 1
            return 0
        return -1

    def enterNumber(self):
        "Finish the entry of a number."
        if self.editingStack:
            self._checkpoint()
            self.s[self.stackPosn].finishEntry()
            self.editingStack = False
            self.cursorPosn = 0

    def undo(self):
        "Return to last stack state in stackCheckpoints."
        self = self.lastStack

    def openNewStackItem(self, c):
        """
        Start a new item on the stack with the given character /c/. Return
        False if we have exceeded the maximum capacity of the stack.
        """
        if self.stackPosn > STACKDEPTH - 2:
            return False

        self.stackPosn += 1
        self.cursorPosn = 0
        self.s.append(StackItem(firstchar=c))
        self.editingStack = True
        return True

    def deleteEndOfStack(self):
        """
        Delete the last item on the stack, for use when it is backspaced
        completely.
        """

        self.stackPosn -= 1
        self.s.pop()
        self.editingStack = False
        self.cursorPosn = 0

    def _checkpoint(self, clearRedoList=True):
        """Save current stack state to global undo list."""
        global stackCheckpoints, redoCheckpoints
        stackCheckpoints.append(copy.deepcopy(self))
        if clearRedoList:
            redoCheckpoints = []

    def push(self, vals):
        for i in vals:
            self.s.append(StackItem(floatval=i))
        self.stackPosn += len(vals)
        #val = ftostr(val)
        #stackw.addstr(1 + ss.stackPosn, 1, val)

    def pop(self, num=1):
        self.stackPosn -= num
        return [self.s.pop().value for i in range(num)]


def ftostr(f):
    """
    Convert a floating-point number to a string. It will be formatted as an
    integer if it has no significant decimal part, and a float otherwise.
    """

    if f.is_integer():
        return str(int(f))
    else:
        return str(f)


def populateCommandsWindow(win, mode='normal', opts={}):
    def addCommand(char, descr, yposn, xposn):
        win.addstr(yposn, xposn, char, curses.color_pair(2))
        win.addstr(yposn, xposn + 1 + len(char), descr)

    win.clear()
    win.border()
    win.addstr(0, 8, "Commands")

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
        win.addstr(1, 6, "(trig mode)")
        win.addstr(2, 6, " [%s] " % opts['mode'] )
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
        win.addstr(1, 7, "(log mode)")
        addCommand("l", "log x", 3, 1 + CENTERFACTOR)
        addCommand("1", "10^x", 4, 1 + CENTERFACTOR)
        addCommand("e", "ln x", 5, 1 + CENTERFACTOR)
        addCommand("n", "e^x", 6, 1 + CENTERFACTOR)
        addCommand("q", "cancel", 7, 1 + CENTERFACTOR)

    elif mode == 'cst':
        CENTERFACTOR = 1
        win.addstr(1, 4, "(constant mode)")
        addCommand("p", "pi", 3, 1 + CENTERFACTOR)
        addCommand("e", "e", 4, 1 + CENTERFACTOR)
        addCommand("q", "cancel", 5, 1 + CENTERFACTOR)

    else:
        assert False, "Invalid mode used for populateCommandsWindow()"

    win.refresh()

def isNumber(c):
    if (c >= '0' and c <= '9') or c == '.' or c == '_' or c == "e":
        return True
    else:
        return False

def changeStatusChar(statusw, c):
    """Place the indicated character /c/ in the status bracket."""
    statusw.addstr(0,1,c, curses.color_pair(1))
    statusw.refresh()

def changeStatusMsg(statusw, msg):
    statusw.addstr(0, 15, ' ' * (80 - 15), curses.color_pair(1))
    statusw.addstr(0, 15, msg, curses.color_pair(1))
    statusw.refresh()

def main(statusw, stackw, commandsw):
    errorState = False
    ss = StackState()
    from functions import fm

    while True:
        # restore status bar after one successful action
        if not errorState:
            changeStatusMsg(statusw, "Ready")
        errorState = False

        # update cursor posn and fetch one char of input
        stackw.move(1 + ss.stackPosn, ss.cursorPosn + 1)
        if not ss.editingStack:
            # when not editing a number, cursor goes on *next line*
            stackw.move(2 + ss.stackPosn, ss.cursorPosn + 1)
            changeStatusChar(statusw, ' ')
        else:
            changeStatusChar(statusw, 'i')
        c = stackw.getch()

        # if we don't have a menu open, try interpreting as a number
        if not fm.curMenu:
            # work around a dumb terminal bug where pressing a WM modkey
            # command at a getch prompt causes the application to crash
            try:
                char = chr(c)
            except ValueError:
                continue
            if isNumber(char):
                if char == '_':
                    char = '-' # negative sign, like dc
                if ss.editingStack:
                    ss.s[ss.stackPosn].addChar(char)
                else:
                    ok = ss.openNewStackItem(char)
                    if not ok: # no more space on the stack
                        changeStatusMsg(statusw, "Stack is full.")
                        errorState = True
                        continue
                    stackw.move(1 + ss.stackPosn, ss.cursorPosn + 1)

                stackw.addstr(char)
                ss.cursorPosn += 1
                continue

            # special number-entering functions
            if c == ord('\n'):
                if ss.editingStack:
                    ss.enterNumber()
                else:
                    changeStatusMsg(statusw, "No number to finish adding. " \
                                             "(Use 'd' to duplicate bos.)")
                    errorState = True
                continue

            elif c == curses.KEY_BACKSPACE or c == 127:
                r = ss.backspace()
                if r == 0:
                    stackw.addstr(1 + ss.stackPosn, ss.cursorPosn + 1, ' ')
                    stackw.move(1 + ss.stackPosn, ss.cursorPosn + 1)
                elif r == 1:
                    stackw.addstr(2 + ss.stackPosn, ss.cursorPosn + 1, ' ')
                    stackw.move(2 + ss.stackPosn, ss.cursorPosn + 1)
                continue


        # If not a number, it's an operator of some kind.
        if fm.runFunction(chr(c), ss):
            redrawStackWin(ss, stackw)
            # find a way to set errorState here: maybe put this last
        else:
            # some error was fired
            errorState = True
            #char = "\\n" if chr(c) == '\n' else chr(c)
            #changeStatusMsg(statusw, "Unrecognized command '%s'." % char)

        if c == ord('q') and fm.quitAfter:
            return

def redrawStackWin(ss, stackw):
    stackw.clear()
    stackw.border()
    stackw.addstr(0, 9, "Stack")
    for i in range(len(ss.s)):
        stackw.addstr(1 + i, 1, ss.s[i].entry)

def setup(stdscr):
    maxy, maxx = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

    status = curses.newwin(1, maxx, 0, 0)
    #status.addstr(0, 0, (' ' * (maxx - 1)), curses.color_pair(1))
    #DEBUG, to see where 80 cols is:
    status.addstr(0, 0, (' ' * 80), curses.color_pair(1))
    status.addstr(0, 0, "[ ] ic 0.0.1 |", curses.color_pair(1))
    status.move(0, 1)

    stack = curses.newwin(3 + STACKDEPTH, 24, 1, 0)
    stack.border()
    stack.addstr(0, 9, "Stack")

    history = curses.newwin(3 + STACKDEPTH, 32, 1, 24)
    history.border()
    history.addstr(0, 13, "History")

    commands = curses.newwin(3 + STACKDEPTH, 24, 1, 56)
    populateCommandsWindow(commands)

    #registers = curses.newwin(maxy - (3 + STACKDEPTH), maxx, 4 + STACKDEPTH, 0)
    registers = curses.newwin(maxy - 1 - (3 + STACKDEPTH), 80, 4 + STACKDEPTH, 0)
    registers.border()
    registers.addstr(0, 36, "Registers")

    stack.refresh()
    status.refresh()
    history.refresh()
    commands.refresh()
    registers.refresh()

    main(status, stack, commands)

if __name__ == "__main__":
    curses.wrapper(setup)
