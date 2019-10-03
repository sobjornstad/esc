"""
util.py - miscellaneous numeric utility functions
"""

import curses
import decimal
import inspect
import itertools
import sys

from consts import REQUIRED_TERM_HEIGHT, REQUIRED_TERM_WIDTH
from oops import ProgrammingError


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


def partition(pred, iterable):
    """
    Use a predicate to partition entries into false entries and true entries.
    Itertools recipe from the standard library documentation.
    """
    t1, t2 = itertools.tee(iterable)
    return itertools.filterfalse(pred, t1), filter(pred, t2)


def magic_call(func, available_kwargs):
    """
    Call /func/, allowing it to pick and choose from a set of arguments. This
    works much like pytest's test fixtures do -- the framework has a set of
    available data or functions which are selected by name by user functions.

    /available_kwargs/ is a dictionary-like object mapping parameter names to
    values. magic_call double-splats these values to any matching arguments
    in the function's signature, ignoring any that aren't named in the
    signature.

    If the function's signature contains an argument that isn't in the
    dictionary, and thus can't be bound, raise a ProgrammingError.
    """
    sig = inspect.signature(func)
    unavailable, requested = (list(i)
                              for i in partition(available_kwargs.__contains__,
                                                 sig.parameters.keys()))

    if unavailable:
        raise ProgrammingError(
            f"The function '{func.__name__}' "
            f"({inspect.getfile(func)}:{inspect.getsourcelines(func)[1]}) "
            f"requested the following arguments which are not available: "
            f"{', '.join(unavailable)}. "
            f"Available arguments are as follows: "
            f"{', '.join(available_kwargs.keys())}.")

    return func(**{k: v for k, v in available_kwargs.items()
                   if k in requested})
