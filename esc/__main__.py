#!/usr/bin/env python3
"""
main.py - startup code and main loop for esc
"""

import curses
import curses.ascii
import datetime
import decimal
from pathlib import Path
from traceback import format_exc
import sys

from .commands import main_menu
from .consts import (UNDO_CHARACTER, REDO_CHARACTER, STORE_REG_CHARACTER,
                     RETRIEVE_REG_CHARACTER, DELETE_REG_CHARACTER, PRECISION)
from . import display
from .display import screen, fetch_input
from . import function_loader
from .helpme import get_help
from . import history
from .oops import (FunctionExecutionError, InvalidNameError, NotInMenuError,
                   RollbackTransaction)
from . import registers
from . import stack
from .status import status
from . import util


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
        if not ss.add_character(char):
            if ss.editing_last_item:
                status.error("No more precision available. "
                             "Consider scientific notation.")
            else:
                status.error("Stack is full.")
                screen().place_cursor(ss)
            return True

        screen().putch_stack(char)
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


def _get_register_char():
    "Retrieve a character representing a register."
    status.expecting_register()
    screen().refresh_status()
    return chr(fetch_input(True))


def _get_help_char():
    "Retrieve a character representing a register."
    status.expecting_help()
    screen().refresh_status()
    return chr(fetch_input(True))


def store_register(ss, registry):
    """
    Copy the bottom of the stack into a register of the user's choice.
    """
    if ss.is_empty:
        status.error("You must have an item on the stack to store to a register.")
        return

    with ss.transaction():
        ss.enter_number()
        reg_char = _get_register_char()
        try:
            registry[reg_char] = ss.bos
        except InvalidNameError as e:
            raise RollbackTransaction(str(e))
        screen().update_registers(registry)
        status.ready()


def retrieve_register(ss, registry):
    """
    Copy a register of the user's choice to a new item at the bottom of the
    stack.
    """
    with ss.transaction():
        ss.enter_number()
        reg_char = _get_register_char()
        try:
            stack_item = registry[reg_char]
        except KeyError:
            raise RollbackTransaction(f"Register '{reg_char}' does not exist.")
        if not ss.push((stack_item,)):
            raise RollbackTransaction("Stack is full.")
        screen().refresh_stack(ss)
        status.ready()


def delete_register(ss, registry):
    """
    Delete a register of the user's choice.
    """
    with ss.transaction():
        ss.enter_number()
        reg_char = _get_register_char()
        try:
            del registry[reg_char]
        except KeyError:
            raise RollbackTransaction(f"Register '{reg_char}' does not exist.")
        screen().update_registers(registry)
        status.ready()


def try_special(c, ss, registry, menu):
    """
    Handle special values that aren't digits to be entered or
    operations to be called, e.g., Enter, Backspace, and undo.

    Returns True if the value was handled, False if not.
    """
    if chr(c) in ('\n', ' '):
        if enter_new_number(ss) is False:
            # could also be None, which would be different
            return True
    elif c in (curses.KEY_BACKSPACE, 127):
        r = ss.backspace()
        screen().backspace(ss, r)
    elif chr(c) == UNDO_CHARACTER:
        if history.hs.undo(ss):
            screen().refresh_stack(ss)
        else:
            status.error("Nothing to undo.")
    elif curses.ascii.unctrl(c) == REDO_CHARACTER:
        if history.hs.redo(ss):
            screen().refresh_stack(ss)
        else:
            status.error("Nothing to redo.")
    elif chr(c) == STORE_REG_CHARACTER:
        store_register(ss, registry)
    elif chr(c) == RETRIEVE_REG_CHARACTER:
        retrieve_register(ss, registry)
    elif chr(c) == DELETE_REG_CHARACTER:
        delete_register(ss, registry)
    elif c == curses.KEY_F1:
        with status.save_state():
            help_on = _get_help_char()
            get_help(help_on, menu, ss, registry)
        screen().refresh_all()
    else:
        return False
    return True


def setup_decimal_context():
    """
    Set up the Context for decimal arithmetic for this thread.
    """
    context = decimal.getcontext()
    context.prec = PRECISION
    context.traps[decimal.Overflow] = 0  # return infinity


def user_loop(ss, registry):
    """
    Main loop to retrieve user input and perform calculator operations.
    """
    menu = None
    while True:
        status.mark_seen()
        screen().refresh_status()
        screen().update_history(ss)

        if menu is None:
            menu = main_menu
        screen().display_menu(menu)

        # Update cursor posn and fetch one char of input.
        screen().place_cursor(ss)
        if menu is main_menu:
            c = fetch_input(False)

            # Are we entering a number?
            r = try_add_to_number(c, ss)
            if r:
                continue

            # Or a special value like backspace or undo?
            r = try_special(c, ss, registry, menu)
            if r:
                continue
        else:
            status.in_menu()
            screen().refresh_status()
            c = fetch_input(True)

        # Try to interpret the input as a function.
        try:
            menu = menu.execute(chr(c), ss, registry)
        except (NotInMenuError, FunctionExecutionError) as e:
            status.error(str(e))
            screen().refresh_status()
        else:
            screen().refresh_stack(ss)
            screen().update_registers(registry)
            status.ready()


def main():
    """
    Initializes the important constructs and launches the main loop.
    """
    setup_decimal_context()
    function_loader.load_all()
    main_menu.test()
    history.hs.clear()  # destroy undo history from tests

    ss = stack.StackState()
    registry = registers.Registry()

    try:
        user_loop(ss, registry)
    except Exception:
        path = Path.home() / ".esc_dump.txt"
        with open(path, 'a') as f:
            f.write(f"\n--- Error dump at {datetime.datetime.now()} ---\n")
            f.write(f"Stack:\n")
            for stackitem in ss.s:
                f.write(str(stackitem) + "\n")
            f.write(f"\nRegisters:\n")
            for k, v in registry.items():
                f.write(f"{k} = {v}\n")
            f.write(f"\nException:\n")
            f.write(format_exc())

        curses.endwin()
        sys.stderr.write("*" * 80 + "\n")
        sys.stderr.write("Something went wrong, sorry about that!\n")
        sys.stderr.write(
            "The error message below may provide some insight into the problem.\n")
        sys.stderr.write(
            "Your current stack and registers and a log of this error "
            "have been written to ~/.esc_dump.txt.\n")
        sys.stderr.write(
            "You can recover your work if necessary by looking in that file.\n\n")
        raise


def bootstrap(stdscr):
    """
    Curses application-bootstrap function.
    """
    display.init(stdscr)
    main()


def curses_wrapper():
    curses.wrapper(bootstrap)


if __name__ == '__main__':
    curses_wrapper()
