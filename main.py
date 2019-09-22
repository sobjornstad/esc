#!/usr/bin/env python3
"""
main.py - startup code and main loop for esc
"""

import curses
import curses.ascii

import display
from display import screen
import menus
import history
import stack
import status
import util
from consts import UNDO_CHARACTER, REDO_CHARACTER
from oops import FunctionExecutionError, NotInMenuError


def fetch_input(in_menu):
    """
    Get one character of input, the location of the window to fetch from
    depending on whether we currently have a menu open (with a menu open, the
    cursor sits in the status bar).
    """
    if in_menu:
        return screen().getch_status()
    else:
        return screen().getch_stack()


def try_add_to_number(c, ss):
    """
    Try to interpret the character /c/ as a digit and add it to the current
    stack item in /ss/ (or create a new stack item).

    Return:
        True if this addition was handled (whether it succeeded or not).
        False if this addition was unhandled.

    State change:
        If the character is handled, the StackState is updated to include
        the newly entered digit.
    """
    try:
        char = chr(c)
    except ValueError:
        return False

    if util.is_number(char):
        if char == '_':
            char = '-' # negative sign, like dc
        if ss.editing_last_item:
            if not ss.s[ss.stack_posn].add_character(char):
                # No more stack width left.
                status.error("No more precision available. "
                             "Consider scientific notation.")
                return True
        else:
            ok = ss.add_partial(char)
            if not ok: # no more space on the stack
                status.error("Stack is full.")
                return True
            screen().place_cursor(ss)

        screen().putch_stack(char)
        ss.cursor_posn += 1
        return True
    return False


def enter_new_number(ss):
    """
    Add any digits that are being entered to a new item on the Stack.
    """
    if ss.editing_last_item:
        r = ss.enter_number()
        # representation might have changed; e.g. user enters 3.0,
        # calculator displays it as 3
        screen().refresh_stack(ss)
    else:
        status.error("No number to finish adding. (Use 'd' to duplicate bos.)")
        r = False
    return r


def try_special(c, ss):
    """
    Handle special values that aren't digits to be entered or
    functions/operations to be called, e.g., Enter, Backspace, and undo.

    Returns True if the value was handled, False if not.
    """
    if chr(c) in ('\n', ' '):
        if enter_new_number(ss) is False:
            # could also be None, which would be different
            return False
    elif c in (curses.KEY_BACKSPACE, 127):
        r = ss.backspace()
        screen().backspace(ss, r)
    elif chr(c) == UNDO_CHARACTER:
        if history.hs.undo_to_checkpoint(ss):
            screen().refresh_stack(ss)
        else:
            status.error("Nothing to undo.")
    elif curses.ascii.unctrl(c) == REDO_CHARACTER:
        if history.hs.redo_to_checkpoint(ss):
            screen().refresh_stack(ss)
        else:
            status.error("Nothing to redo.")
    else:
        return False
    return True


def main():
    """
    Where the magic happens. Initializes the important constructs and manages
    the main loop.
    """
    ss = stack.StackState()
    menu = None

    # Main loop.
    while True:
        status.mark_seen()
        status.redraw()

        if menu is None:
            menu = menus.main_menu
        menus.display_menu(menu)

        # Update cursor posn and fetch one char of input.
        screen().place_cursor(ss)
        if menu is menus.main_menu:
            c = fetch_input(False)

            # Are we entering a number?
            r = try_add_to_number(c, ss)
            if r:
                continue

            # Or a special value like backspace or undo?
            r = try_special(c, ss)
            if r:
                continue
        else:
            status.in_menu()
            status.redraw()
            c = fetch_input(True)

        # Try to interpret the input as a function.
        try:
            menu = menu.execute(chr(c), ss)
        except (NotInMenuError, FunctionExecutionError) as e:
            status.error(str(e))
            status.redraw()
        else:
            screen().refresh_stack(ss)
            #TODO: This shouldn't go to ready() if there was an advisory or
            # error within the function
            status.ready()


def bootstrap(stdscr):
    """
    Curses application-bootstrap function.
    """
    display.init(stdscr)
    main()


if __name__ == "__main__":
    curses.wrapper(bootstrap)
