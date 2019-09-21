#!/usr/bin/env python3

import curses
import curses.ascii

import display
from display import screen
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
            screen().set_status_msg("Ready")
        errorState = False

        # update cursor posn and fetch one char of input (in stack or status)
        screen().place_cursor(ss)
        if fm.curMenu:
            c = screen().getch_status()
        else:
            c = screen().getch_stack()

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
                        screen().set_status_msg("No more precision available." \
                                " (You can use scientific notation.)")
                        errorState = True
                        continue
                else:
                    ok = ss.openNewStackItem(char)
                    if not ok: # no more space on the stack
                        screen().set_status_msg("Stack is full.")
                        errorState = True
                        continue
                    screen().place_cursor(ss)

                screen().putch_stack(char)
                ss.cursorPosn += 1
                continue

            # more number-entering functions
            if c == ord('\n') or c == ord(' '):
                if ss.editingStack:
                    r = ss.enterNumber()
                    # representation might have changed; e.g. user enters 3.0,
                    # calculator displays it as 3
                    screen().refresh_stack(ss)
                else:
                    screen().set_status_msg(
                        "No number to finish adding. (Use 'd' to duplicate bos.)")
                    r = False
                if r is False: # could also be None, which would be different
                    errorState = True
                continue
            elif c == curses.KEY_BACKSPACE or c == 127:
                r = ss.backspace()
                screen().backspace(ss, r)
                continue

        # or do we want to undo?
        if chr(c) == UNDO_CHARACTER:
            newSs = history.hs.lastCheckpoint(ss)
            if newSs:
                ss = newSs
                screen().refresh_stack(ss)
            else:
                screen().set_status_msg("Nothing to undo.")
                errorState = True
            continue
        elif curses.ascii.unctrl(c) == REDO_CHARACTER:
            newSs = history.hs.nextCheckpoint(ss)
            if newSs:
                ss = newSs
                screen().refresh_stack(ss)
            else:
                screen().set_status_msg("Nothing to redo.")
                errorState = True
            continue


        # Otherwise, it's an operator of some kind.
        if fm.runFunction(chr(c), ss):
            screen().refresh_stack(ss)
        else:
            # either there was an error, or we simply wanted to display output
            # on the status bar.
            errorState = True

        # if, within fm, we chose to quit, quit.
        if fm.quitAfter:
            return

def bootstrap(stdscr):
    display.init(stdscr)
    main()

if __name__ == "__main__":
    curses.wrapper(bootstrap)
