#!/usr/bin/env python3

import curses
import curses.ascii

import display
from display import screen
import functionmanagement
import history
import stack
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
        True if this addition was successful.
        False if this addition caused an error.
        None if the character was not handled by this function.
    
    State change:
        If the character is handled, the StackState is updated to include
        the newly entered digit.
    """
    try:
        char = chr(c)
    except ValueError:
        return False

    if util.isNumber(char):
        if char == '_':
            char = '-' # negative sign, like dc
        if ss.editing_last_item:
            if not ss.s[ss.stack_posn].add_character(char):
                # no more stack width left
                screen().set_status_msg(
                    "No more precision available. Consider scientific notation.")
                return False
        else:
            ok = ss.add_partial(char)
            if not ok: # no more space on the stack
                screen().set_status_msg("Stack is full.")
                return False
            screen().place_cursor(ss)

        screen().putch_stack(char)
        ss.cursor_posn += 1
        return True
    return None


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
        screen().set_status_msg(
            "No number to finish adding. (Use 'd' to duplicate bos.)")
        r = False
    return r


def try_special(c, ss):
    """
    Handle special values that aren't digits to be entered or
    functions/operations to be called, e.g., Enter, Backspace, and undo.
    """
    if chr(c) in ('\n', ' '):
        if enter_new_number(ss) is False:
            # could also be None, which would be different
            return False
        return True
    elif c in (curses.KEY_BACKSPACE, 127):
        r = ss.backspace()
        screen().backspace(ss, r)
        return True
    elif chr(c) == UNDO_CHARACTER:
        if history.hs.undo_to_checkpoint(ss):
            screen().refresh_stack(ss)
            return True
        else:
            screen().set_status_msg("Nothing to undo.")
            return False
    elif curses.ascii.unctrl(c) == REDO_CHARACTER:
        if history.hs.redo_to_checkpoint(ss):
            screen().refresh_stack(ss)
            return True
        else:
            screen().set_status_msg("Nothing to redo.")
            return False
    else:
        return None


def main():
    """
    Where the magic happens. Initializes the important constructs and manages
    the main loop.
    """
    errorState = False
    ss = stack.StackState()
    menu = None

    # Main loop.
    while True:
        # Restore status bar after one successful action.
        if not errorState:
            screen().set_status_msg("Ready")
        errorState = False

        if menu is None:
            menu = functionmanagement.main_menu
        functionmanagement.display_menu(menu)

        # Update cursor posn and fetch one char of input.
        screen().place_cursor(ss)
        c = fetch_input(menu is not functionmanagement.main_menu)

        if menu is functionmanagement.main_menu:
            # Are we entering a number?
            r = try_add_to_number(c, ss)
            if r is not None:
                errorState = not r
                continue

            # Or a special value like backspace or undo?
            r = try_special(c, ss)
            if r is not None:
                errorState = not r
                continue

        # If it wasn't one of those, try to interpret it as a function.
        try:
            menu = menu.execute(chr(c), ss)
            screen().refresh_stack(ss)
        except (NotInMenuError, FunctionExecutionError) as e:
            errorState = True
            screen().set_status_msg(str(e))

        # If we chose to quit, quit. This is managed within 'fm' because it's
        # used both for leaving menus and for quitting the whole program.
        #if fm.quitAfter:
        #    return


def bootstrap(stdscr):
    """
    Curses application-bootstrap function.
    """
    display.init(stdscr)
    main()


if __name__ == "__main__":
    curses.wrapper(bootstrap)
