#!/usr/bin/env python3

#TODO:
# History section.
# Registers.
# Don't crash when a menu is registered without any content
# Also, make sure descriptions are not too long to fit
# Dev documentation (maybe program some of my own functions)

import curses
import curses.ascii

import display
import history
import stack
import util
from consts import UNDO_CHARACTER, REDO_CHARACTER

def main():
    errorState = False
    ss = stack.StackState()

    from functions import fm # adds all functions in functions.py to fm
    fm.displayMenu()

    while True:
        # restore status bar after one successful action
        if not errorState:
            display.changeStatusMsg("Ready")
        errorState = False

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
            if util.isNumber(char):
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
                    # calculator displays it as 3
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
            # either there was an error, or we simply wanted to display output
            # on the status bar.
            errorState = True

        # if, within fm, we chose to quit, quit.
        if fm.quitAfter:
            return

def bootstrap(stdscr):
    display.setup(stdscr)
    main()

if __name__ == "__main__":
    curses.wrapper(bootstrap)
