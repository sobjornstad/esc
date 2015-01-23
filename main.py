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

def pushOnto(val, ss, stackw):
    "Push a given float onto the stack."
    # Duplicating as a method -- we want to move to force refresh otherwise

    ss.s.append(StackItem(floatval=val))
    ss.stackPosn += 1
    val = ftostr(val)
    stackw.addstr(1 + ss.stackPosn, 1, val)

def unaryOperator(ss, stackw, opfn):
    """
    Just like binaryOperator, except only one item is pulled off the bottom of
    the stack and the opfn thus only takes one argument.
    """

    if len(ss.s) < 1:
        return None

    bos = ss.s.pop()
    stackw.addstr(1 + ss.stackPosn, 1, ' ' * bos.getReprStrlen())
    ss.stackPosn -= 1

    result = opfn(bos.value)
    pushOnto(result, ss, stackw)

    return ss

def binaryOperator(ss, stackw, opfn):
    """
    Run the passed function /opfn/ on the stack in StackState /ss/. Update the
    stack as well as the representation of the stack on window /stackw/, and
    return the updated StackState. If there are not at least two items on the
    stack, return None.

    The opfn should take two arguments, /sos/ (second on stack) and /bos/
    (bottom of stack) and return a float to be pushed noto the stack.
    """

    if len(ss.s) < 2:
        return None

    # pop values off stack
    bos = ss.s.pop() # bottom of stack
    sos = ss.s.pop() # second on stack

    # blank out old portion of stack
    stackw.addstr(1 + ss.stackPosn, 1, ' ' * bos.getReprStrlen())
    stackw.addstr(ss.stackPosn, 1, ' ' * sos.getReprStrlen())
    ss.stackPosn -= 2

    # calculate and push result
    result = opfn(sos.value, bos.value)
    pushOnto(result, ss, stackw)

    return ss

def changeStatusChar(statusw, c):
    """Place the indicated character /c/ in the status bracket."""
    statusw.addstr(0,1,c, curses.color_pair(1))
    statusw.refresh()

def changeStatusMsg(statusw, msg):
    statusw.addstr(0, 15, ' ' * (80 - 15), curses.color_pair(1))
    statusw.addstr(0, 15, msg, curses.color_pair(1))
    statusw.refresh()


def clip(str, p=True, c=True):
    # http://stackoverflow.com/questions/7606062/
    # is-there-a-way-to-directly-send-a-python-output-to-clipboard
    "Use xsel to yank a string to the clipboard on Unix."
    from subprocess import Popen, PIPE
    if p:
        p = Popen(['xsel', '-pi'], stdin=PIPE)
        p.communicate(input=str)
    if c:
        p = Popen(['xsel', '-bi'], stdin=PIPE)
        p.communicate(input=str)

def trigMenu(statusw, stackw, commandsw, ss):
    "Handle the trig mode. Return new stack state."

    populateCommandsWindow(commandsw, mode='trig', opts={'mode': ss.trigMode})
    changeStatusMsg(statusw, "Expecting trig command (q cancels)")
    while True:
        fn = statusw.getch(0, 1)
        if chr(fn) not in ('s', 'c', 't', 'i', 'o', 'a', 'r', 'd', 'q'):
            char = "\\n" if chr(fn) == '\n' else chr(fn)
            changeStatusMsg(statusw, "Invalid trig mode command " \
                                     "'%s' (q cancels)" % char)
        else:
            if fn == ord('r'):
                ss.trigMode = 'radians'
                break
            elif fn == ord('d'):
                ss.trigMode = 'degrees'
                break

            if ss and ss.trigMode == 'degrees' and chr(fn) in ('s', 'c', 't'):
                # convert bos to radians for following fns
                ss = unaryOperator(ss, stackw, lambda bos: math.radians(bos))

            try:
                if fn == ord('s'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.sin(bos))
                elif fn == ord('c'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.cos(bos))
                elif fn == ord('t'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.tan(bos))
                elif fn == ord('i'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.asin(bos))
                elif fn == ord('o'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.acos(bos))
                elif fn == ord('a'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.atan(bos))
            except ValueError:
                ss = 'error' # force rollback to original stack
                changeStatusMsg(statusw,
                        "'t': Domain error! Stack unchanged.")
                break

            if ss and ss.trigMode == 'degrees' and chr(fn) in ('i', 'o', 'a'):
                # convert radian result to degrees
                ss = unaryOperator(ss, stackw, lambda bos: math.degrees(bos))

            break

    populateCommandsWindow(commandsw)
    return ss

def logMenu(statusw, stackw, commandsw, ss):
    "Handle the log mode. Return new stack state."

    populateCommandsWindow(commandsw, mode='log')
    changeStatusMsg(statusw, "Expecting log command (q cancels)")
    while True:
        fn = statusw.getch(0, 1)
        if chr(fn) not in ('l', '1', 'e', 'n', 'q'):
            char = "\\n" if chr(fn) == '\n' else chr(fn)
            changeStatusMsg(statusw, "Invalid log mode command " \
                                     "'%s' (q cancels)" % char)
        else:
            try:
                if fn == ord('l'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.log10(bos))
                elif fn == ord('1'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.pow(10,bos))
                elif fn == ord('e'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.log(bos))
                elif fn == ord('n'):
                    ss = unaryOperator(ss, stackw, lambda bos: math.pow(math.e, bos))
            except ValueError:
                ss = 'error' # force rollback to original stack
                changeStatusMsg(statusw,
                        "'l': Domain error! Stack unchanged.")
                break

            if ss and ss.trigMode == 'degrees' and chr(fn) in ('i', 'o', 'a'):
                # convert radian result to degrees
                ss = unaryOperator(ss, stackw, lambda bos: math.degrees(bos))

            break

    populateCommandsWindow(commandsw)
    return ss

def cstMenu(statusw, stackw, commandsw, ss):
    "Handle insertion of constants. Return new stack state."

    populateCommandsWindow(commandsw, mode='cst')
    changeStatusMsg(statusw, "Expecting constant choice (q cancels)")
    while True:
        fn = statusw.getch(0, 1)
        if chr(fn) not in ('p', 'e', 'q'):
            char = "\\n" if chr(fn) == '\n' else chr(fn)
            changeStatusMsg(statusw, "Invalid constant choice " \
                                     "'%s' (q cancels)" % char)
        else:
            if ss.stackPosn > STACKDEPTH - 2:
                changeStatusMsg(statusw, "'i': Stack is full.")
                populateCommandsWindow(commandsw)
                return 'error'

            if fn == ord('p'):
                pushOnto(math.pi, ss, stackw)
            elif fn == ord('e'):
                pushOnto(math.e, ss, stackw)

            populateCommandsWindow(commandsw)
            return ss

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

        # entry of a number
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

        elif c == curses.KEY_BACKSPACE or c == 127:
            r = ss.backspace()
            if r == 0:
                stackw.addstr(1 + ss.stackPosn, ss.cursorPosn + 1, ' ')
                stackw.move(1 + ss.stackPosn, ss.cursorPosn + 1)
            elif r == 1:
                stackw.addstr(2 + ss.stackPosn, ss.cursorPosn + 1, ' ')
                stackw.move(2 + ss.stackPosn, ss.cursorPosn + 1)



        # try running as an operator; if not, we return False and go on
        elif fm.runFunction(chr(c), ss):
            redrawStackWin(ss, stackw)

        elif chr(c) in ('t', 'i', 'l'):
            numOperands = 1 if chr(c) in ('s', 't') else 2
            oldSs = copy.deepcopy(ss)
            ss.enterNumber()
            if c == ord('s'):
                try:
                    ss = unaryOperator(ss, stackw, lambda bos: math.sqrt(bos))
                except ValueError:
                    ss = 'error'
                    changeStatusMsg(statusw,
                            "'s': Domain error! Stack unchanged.")
            elif c == ord('t'):
                ss = trigMenu(statusw, stackw, commandsw, ss)
            elif c == ord('i'):
                ss = cstMenu(statusw, stackw, commandsw, ss)
            elif c == ord('l'):
                ss = logMenu(statusw, stackw, commandsw, ss)

            if not ss:
                ss = oldSs
                msg = "'" + chr(c) + "': "
                if numOperands == 2 and len(ss.s) > 0:
                    msg += "Only one item on stack."
                else:
                    msg += "Stack is empty."
                if chr(c) == '-':
                    msg += " (Did you mean '_'?)"

                changeStatusMsg(statusw, msg)
                errorState = True
            elif ss == 'error':
                # code that sets this displays error message, we do the rest
                ss = oldSs
                redrawStackWin(ss, stackw)
                errorState = True


        # stack operations
        elif c == ord('u'):
            if stackCheckpoints:
                global redoCheckpoints
                redoCheckpoints.append(copy.deepcopy(ss))
                ss = stackCheckpoints.pop()
                redrawStackWin(ss, stackw)
            else:
                changeStatusMsg(statusw, "Nothing to undo.")
                errorState = True
        elif curses.ascii.unctrl(c) == "^R":
            if redoCheckpoints:
                # save redo checkpoint
                ss._checkpoint(clearRedoList=False)
                ss = redoCheckpoints.pop()
                redrawStackWin(ss, stackw)
            else:
                changeStatusMsg(statusw, "Nothing to redo.")
                errorState = True
        elif c == ord('y'):
            ss.enterNumber()
            try:
                bos = ss.s[-1]
            except IndexError:
                changeStatusMsg(statusw, "Nothing on stack to yank.")
                errorState = True
                continue
            clip(ftostr(bos.value), p=False)

        # program functions
        elif c == ord('q'):
            return

        else:
            char = "\\n" if chr(c) == '\n' else chr(c)
            errorState = True
            changeStatusMsg(statusw, "Unrecognized command '%s'." % char)

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
