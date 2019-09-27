"""
util.py - miscellaneous numeric utility functions
"""

import curses
import decimal
import display
import sys

from consts import REQUIRED_TERM_HEIGHT, REQUIRED_TERM_WIDTH


def is_number(c):
    return ('0' <= c <= '9') or (c in ('.', '_', 'e'))


def remove_exponent(d):
    """
    Remove exponent and trailing zeros. Modified from the version in the
    decimal docs: if there are not enough digits of precision to express the
    coefficient without scientific notation, don't do anything.

    >>> remove_exponent(decimal.Decimal('5E+3'))
    decimal.Decimal('5000')
    """

    retval = d.normalize()
    if d == d.to_integral():
        try:
            retval = d.quantize(decimal.Decimal(1))
        except decimal.InvalidOperation:
            pass

    return retval


def truncate(string: str, max_length: int) -> str:
    "Truncate /string/ to at most /max_length/ using an ellipsis."
    if len(string) > max_length:
        string = string[:max_length-3] + '...'
    return string


def quit_if_screen_too_small(max_y, max_x):
    """
    If the terminal is too small, quit, providing a useful error message.
    """
    if max_y < REQUIRED_TERM_HEIGHT or max_x < REQUIRED_TERM_WIDTH:
        curses.endwin()
        sys.stderr.write(
            f"esc requires at least a "
            f"{REQUIRED_TERM_WIDTH}x{REQUIRED_TERM_HEIGHT} terminal "
            f"(this terminal is {max_x}x{max_y}).\n")
        sys.exit(1)


def centered_position(text: str, width: int) -> int:
    """
    Return the integer column to start writing a string /text/ at to
    center it within a window of width /width/.
    """
    return (width - len(text)) // 2 + 1


def fetch_input(in_menu) -> int:
    """
    Get one character of input, the location of the window to fetch from
    depending on whether we currently have a menu open (with a menu open, the
    cursor sits in the status bar). The character is returned as an int for
    compatibility with curses functions; use chr() to turn it into a string.
    """
    if in_menu:
        return display.screen().getch_status()
    else:
        return display.screen().getch_stack()

