#!/usr/bin/env python

#TODO:
# History section.
# Registers.
# Logarithm menu.
# Don't panic if stack width exceeded, or if other invalid input
#   (e.g., entering an 'e' where it can't be scientific notation,
#    multiple decimals, negative by itself)
# A bit more documentation
# It's sometimes possible to overflow the stack window? It should do sci notation.
# Fix undoing and checkpoints; it fails at many important operations.

import curses.wrapper
import curses.ascii
import copy

import display
from consts import STACKDEPTH, STACKWIDTH

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

def isNumber(c):
    if (c >= '0' and c <= '9') or c == '.' or c == '_' or c == "e":
        return True
    else:
        return False

def main():
    errorState = False
    ss = StackState()
    from functions import fm

    while True:
        # restore status bar after one successful action
        if not errorState:
            display.changeStatusMsg("Ready")
        errorState = False

        # update cursor posn and fetch one char of input
        display.adjustCursorPos(ss)
        c = display.getch_stack()

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
                        display.changeStatusMsg("Stack is full.")
                        errorState = True
                        continue
                    display.defaultStackCursorPos(ss)

                display.putch_stack(char)
                ss.cursorPosn += 1
                continue

            # special number-entering functions
            if c == ord('\n'):
                if ss.editingStack:
                    ss.enterNumber()
                else:
                    display.changeStatusMsg("No number to finish adding. " \
                                             "(Use 'd' to duplicate bos.)")
                    errorState = True
                continue

            elif c == curses.KEY_BACKSPACE or c == 127:
                r = ss.backspace()
                display.displayBackspace(ss, r)
                continue


        # If not a number, it's an operator of some kind.
        if fm.runFunction(chr(c), ss):
            display.redrawStackWin(ss)
            # find a way to set errorState here: maybe put this last
        else:
            # some error was fired
            errorState = True
            #char = "\\n" if chr(c) == '\n' else chr(c)
            #changeStatusMsg("Unrecognized command '%s'." % char)

        if c == ord('q') and fm.quitAfter:
            return

def bootstrap(stdscr):
    display.setup(stdscr)
    main()

if __name__ == "__main__":
    curses.wrapper(bootstrap)
