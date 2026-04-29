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
                     RETRIEVE_REG_CHARACTER, DELETE_REG_CHARACTER, PRECISION,
                     UNIT_ENTRY_CHARACTER)
from . import display
from .display import screen, fetch_input
from . import function_loader
from .helpme import get_help
from . import history
from .oops import (FunctionExecutionError, InvalidNameError, NotInMenuError,
                   RollbackTransaction, UnitError)
from . import registers
from . import stack
from .status import status
from .units import UnitExpression
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
            status.error("No more precision available. "
                         "Consider scientific notation.")
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


def _get_help_char(ss, registry, menu):
    "Retrieve a character representing a help topic."
    status.expecting_help()
    screen().refresh_status()
    while True:
        c = fetch_input(True)
        if c == curses.KEY_RESIZE:
            _handle_resize(ss, registry, menu)
            if not screen().too_small:
                status.expecting_help()
                screen().refresh_status()
            continue
        return chr(c)


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
        ss.push((stack_item,))
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


# Override tracking for unit errors
_last_unit_error = None  # (menu_id, key, error_type) or None


def _enter_unit_mode(ss, registry, menu):
    """
    Enter unit annotation mode. Collects characters into a buffer,
    parses as a UnitExpression on finish, and attaches to bos.
    """
    if ss.is_empty:
        status.error("No item on stack to tag with a unit.")
        return

    # If editing a number, finish entry first
    if ss.editing_last_item:
        try:
            ss.enter_number()
        except ValueError as e:
            status.error(str(e))
            return
        screen().refresh_stack(ss)

    status.entering_unit()
    screen().refresh_status()

    # Activate wider stack column early so there's room to type
    screen().activate_units()
    # Refresh all windows after possible layout change
    screen().refresh_status()
    screen().refresh_stack(ss)
    screen().update_history(ss)
    active_menu = menu if menu is not None else main_menu
    screen().display_menu(active_menu)
    screen().update_registers(registry)

    # Lower escape delay so Esc cancels promptly (default ~1000ms)
    old_escdelay = curses.get_escdelay()
    curses.set_escdelay(25)

    buf = ""
    target_item = ss.bos

    # Signal unit-entry mode to the stack window (None = inactive, "" = active)
    screen().stackw.partial_unit = buf
    screen().refresh_stack(ss)

    while True:
        screen().place_cursor(ss)
        c = fetch_input(False)  # read from stack window to keep cursor there

        if c == curses.KEY_RESIZE:
            _handle_resize(ss, registry, menu)
            if not screen().too_small:
                status.entering_unit()
                screen().refresh_status()
                screen().stackw.partial_unit = buf
                screen().refresh_stack(ss)
            continue

        if c == 27:  # Escape — cancel, preserve original unit
            break

        try:
            char = chr(c)
        except (ValueError, OverflowError):
            continue

        if char in ('\n', ' '):
            stripped = buf.strip()
            if not stripped:
                target_item.unit = None
                break
            try:
                unit = UnitExpression.parse(stripped)
            except ValueError as e:
                status.error(f"Invalid unit name: {e}")
                screen().refresh_status()
                continue
            target_item.unit = unit
            break
        elif c in (curses.KEY_BACKSPACE, 127) or curses.ascii.unctrl(c) == '^H':
            if buf:
                # Remove the whole " * " or " / " if we auto-inserted it
                if buf.endswith(' * ') or buf.endswith(' / '):
                    buf = buf[:-3]
                else:
                    buf = buf[:-1]
            else:
                break  # empty buffer, cancel
        elif char == '*':
            buf += " * "
        elif char == '/':
            buf += " / "
        elif char.isprintable():
            buf += char
        else:
            continue  # ignore other chars

        # Show progress inline in the stack
        screen().stackw.partial_unit = buf
        screen().refresh_stack(ss)

    # Restore escape delay and clear partial unit display
    curses.set_escdelay(old_escdelay)
    screen().stackw.partial_unit = None

    screen().refresh_stack(ss)
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
    elif c in (curses.KEY_BACKSPACE, 127) or curses.ascii.unctrl(c) == '^H':
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
    elif chr(c) == UNIT_ENTRY_CHARACTER:
        _enter_unit_mode(ss, registry, menu)
    elif c == curses.KEY_F1:
        with status.save_state():
            help_on = _get_help_char(ss, registry, menu)
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


def _handle_resize(ss, registry, menu):
    """Handle a terminal resize event."""
    screen().handle_resize()
    if not screen().too_small:
        screen().refresh_stack(ss)
        screen().update_registers(registry)
        if menu is not None:
            screen().display_menu(menu)


def user_loop(ss, registry):
    """
    Main loop to retrieve user input and perform calculator operations.
    """
    global _last_unit_error
    menu = None
    while True:
        # If the terminal is too small, wait for a resize event.
        if screen().too_small:
            c = screen().stdscr.getch()
            if c == curses.KEY_RESIZE:
                _handle_resize(ss, registry, menu)
            continue

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

            if c == curses.KEY_RESIZE:
                _handle_resize(ss, registry, menu)
                continue

            # Are we entering a number?
            r = try_add_to_number(c, ss)
            if r:
                _last_unit_error = None
                continue

            # Or a special value like backspace or undo?
            r = try_special(c, ss, registry, menu)
            if r:
                _last_unit_error = None
                continue
        else:
            status.in_menu()
            screen().refresh_status()
            c = fetch_input(True)

            if c == curses.KEY_RESIZE:
                _handle_resize(ss, registry, menu)
                continue

        # Check for unit error override: same menu, same key, same error type
        unit_override = False
        try:
            key_char = chr(c)
        except (ValueError, OverflowError):
            key_char = None

        if (_last_unit_error is not None
                and key_char is not None
                and _last_unit_error == (id(menu), key_char,
                                         _last_unit_error[2])):
            unit_override = True

        _last_unit_error = None

        # Try to interpret the input as a function.
        try:
            menu = menu.execute(chr(c), ss, registry,
                                unit_override=unit_override)
        except UnitError as e:
            _last_unit_error = (id(menu), chr(c), type(e))
            status.error(str(e))
            screen().refresh_status()
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
