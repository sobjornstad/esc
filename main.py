#!/usr/bin/env python

#TODO:
# History section.
# Registers.
# Don't crash when a menu is registered without any content
# Also, make sure descriptions are not too long to fit
# Dev documentation (maybe program some of my own functions)

import curses.wrapper
import curses.ascii
import copy
import decimal
from decimal import Decimal

import display
import history
import util
from consts import STACKDEPTH, STACKWIDTH, UNDO_CHARACTER, REDO_CHARACTER
from time import sleep # debug

class StackItem(object):
    def __init__(self, firstchar=None, decval=None):
        """
        We can create an item on the stack either by the user entering it (in
        which case we have methods for gradually building up a string repr of
        the value and then converting it to the Decimal value that is used for
        calculations) or by directly entering a Decimal value (for instance, as
        the result of a calculation).
        """
        if firstchar is not None:
            self.isEntered = False
            self.entry = firstchar
            self.value = None
        elif decval is not None:
            self.isEntered = True
            self.value = decval
            self._entryFromVal()
        else:
            assert False, "No valid argument to constructor of StackItem!"

    def addChar(self, nextchar):
        """
        Add a character to the running string of the number being entered on
        the stack. Return True if successful, False if the stack width has
        been exceeded.
        """

        assert not self.isEntered, "Number already entered!"
        if len(self.entry) < STACKWIDTH:
            self.entry += nextchar
            return True
        else:
            return False

    def finishEntry(self):
        """
        Convert an entered string to a Decimal value. If successful, return
        True; if the entered string does not form a valid number, return False.
        This should be called from self.enterNumber() and probably nowhere
        else.
        """

        try:
            self.value = Decimal(self.entry)
        except decimal.InvalidOperation:
            return False
        else:
            self._entryFromVal()  # convert string rep to internal display rep
            self.isEntered = True
            return True

    def _entryFromVal(self):
        "(Re)set the /entry/ string based on the attribute /value/."

        self.entry = str(util.remove_exponent(
            self.value.normalize())).replace('E', 'e')

        # if we weren't using scientific notation but the new value is too
        # long to fit in the stack window, convert it, knocking down the
        # displayed precision to fit
        if len(self.entry) > STACKWIDTH:
            precision = STACKWIDTH
            precision -= 3            # account for length of exponent
            precision -= len("0.e+")  # account for new characters
            precision -= (1 if self.value.as_tuple().sign == 1 else 0)
            self.entry = ("%." + str(precision) + "e") % (self.value)


class StackState(object):
    """
    An object containing the current state of the stack: a stack pointer, the
    screen cursor's position across on the current value, the stack itself as a
    list, and whether we are currently editing a number. 

    Values may be manipulated directly as convenient. There are also several
    helper methods for convenience.

    Generally, a StackState object should be initialized at the beginning of
    execution and used until the program exits. Checkpointing and undoing
    operate by copying and restoring the stack state object.
    """

    def __init__(self):
        self.clearStack()

    def clearStack(self):
        "Set up an empty stack, or clear the stack."
        self.s = []
        self.stackPosn = -1
        self.cursorPosn = 0
        self.editingStack = False # whether we are editing a number

    def backspace(self):
        """
        Backspace one character in the current item on the stack. Return 0 if a
        character was backspaced, 1 if the whole item was wiped out, and -1 if
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

    def enterNumber(self, runningOp=None):
        """
        Finish the entry of a number. Returns True if done, False if the value
        was invalid, and None if we were not editing the stack in the first
        place.

        Set runningOp to an operation name if you're entering prior to running
        an operation (go figure) for a more helpful error message in that case.
        """

        # Even if we were *not* editing the stack, checkpoint the stack state.
        # This ensures that we will get a checkpoint anytime we call an
        # operation as well as when we enter a number onto the stack.
        history.hs.checkpointState(self)

        if self.editingStack:
            if self.s[self.stackPosn].finishEntry():
                self.editingStack = False
                self.cursorPosn = 0
                return True
            else:
                if runningOp:
                    msg = 'Cannot run "%s": invalid value on bos.' % runningOp
                else:
                    msg = 'Invalid entry.'
                display.changeStatusMsg(msg)
                return False

    def openNewStackItem(self, c):
        """
        Start a new item on the stack with the given character /c/. Return
        False if we have exceeded the maximum capacity of the stack.
        """

        if not self.enoughPushSpace(1):
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

    def enoughPushSpace(self, num):
        return STACKDEPTH >= len(self.s) + num
    def freeStackSpaces(self):
        return STACKDEPTH - self.stackPosn - 1


    def push(self, vals):
        if not self.enoughPushSpace(len(vals)):
            return False
        # we need to take it in reverse because it's like we're popping from
        # the provided slice of stack
        for i in reversed(vals):
            decval = i
            if type(decval) != Decimal:
                try:
                    decval = Decimal(i)
                except decimal.InvalidOperation as e:
                    assert False, "That operation returned a value that cannot"\
                            " be converted to a Decimal. The original error"   \
                            " message is as follows: %r" % e

            self.s.append(StackItem(decval=decval))
        self.stackPosn += len(vals)
        return True

    def pop(self, num=1):
        self.stackPosn -= num
        oldStack = copy.deepcopy(self.s)
        try:
            return [self.s.pop().value for i in range(num)]
        except IndexError:
            self.s = oldStack
            self.stackPosn += num
            return None

def isNumber(c):
    if (c >= '0' and c <= '9') or c == '.' or c == '_' or c == "e":
        return True
    else:
        return False

def main():
    errorState = False
    ss = StackState()

    from functions import fm # also runs all content in functions module
    fm.displayMenu()

    while True:
        # restore status bar after one successful action
        if not errorState:
            display.changeStatusMsg("Ready")
        errorState = False

        #DEBUG: work out the type errors
        #try:
            #display.changeStatusMsg("bos is %s" % type(ss.s[-1].value))
        #except (IndexError):
            #display.changeStatusMsg("no valid number on bos")

        # update cursor posn and fetch one char of input (in stack or status)
        display.adjustCursorPos(ss)
        if fm.curMenu:
            c = display.getch_status()
        else:
            c = display.getch_stack()

        # if we don't have a menu open, try interpreting as a number
        if not fm.curMenu:
            try:
                char = chr(c)
            except ValueError:
                continue # ignore unrecognized or invalid characters
            if isNumber(char):
                if char == '_':
                    char = '-' # negative sign, like dc
                if ss.editingStack:
                    r = ss.s[ss.stackPosn].addChar(char)
                    if not r:
                        # no more stack width left
                        display.changeStatusMsg("No more precision available." \
                                " (You can use scientific notation.)")
                        errorState = True
                        continue
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

            # more number-entering functions
            if c == ord('\n') or c == ord(' '):
                if ss.editingStack:
                    r = ss.enterNumber()
                    # representation might have changed; e.g. user enters 3.0,
                    # calculator displays it to 3
                    display.redrawStackWin(ss)
                else:
                    display.changeStatusMsg("No number to finish adding. " \
                                             "(Use 'd' to duplicate bos.)")
                    r = False
                if r is False: # could also be None, which would be different
                    errorState = True
                continue
            elif c == curses.KEY_BACKSPACE or c == 127:
                r = ss.backspace()
                display.displayBackspace(ss, r)
                continue

        # or do we want to undo?
        if chr(c) == UNDO_CHARACTER:
            newSs = history.hs.lastCheckpoint(ss)
            if newSs:
                ss = newSs
                display.redrawStackWin(ss)
            else:
                display.changeStatusMsg("Nothing to undo.")
                errorState = True
            continue
        elif curses.ascii.unctrl(c) == REDO_CHARACTER:
            newSs = history.hs.nextCheckpoint(ss)
            if newSs:
                ss = newSs
                display.redrawStackWin(ss)
            else:
                display.changeStatusMsg("Nothing to redo.")
                errorState = True
            continue


        # Otherwise, it's an operator of some kind.
        if fm.runFunction(chr(c), ss):
            display.redrawStackWin(ss)
        else:
            errorState = True

        if c == ord('q') and fm.quitAfter:
            return

def bootstrap(stdscr):
    display.setup(stdscr)
    main()

if __name__ == "__main__":
    curses.wrapper(bootstrap)
