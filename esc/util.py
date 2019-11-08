"""
util.py - miscellaneous numeric utility functions
"""

import curses
import decimal
import inspect
import itertools
import sys

from .consts import REQUIRED_TERM_HEIGHT, REQUIRED_TERM_WIDTH
from .oops import ProgrammingError


def centered_position(text: str, width: int) -> int:
    """
    Return the integer column to start writing a string /text/ at to
    center it within a window of width /width/.

    If width is less than 1 or the text is too long for the provided width,
    AssertionError is raised.

    >>> centered_position("Soren", 11)
    4

    >>> centered_position("Maud", 10)
    4

    >>> centered_position("Soren", 10)
    3

    >>> centered_position("Using it all", 12)
    0

    >>> centered_position("Using it all.", 13)
    0

    >>> centered_position("overwraps", 2)
    Traceback (most recent call last):
      ..
    AssertionError: text 'overwraps' can't fit in 2 columns

    >>> centered_position("Soren", -8)
    Traceback (most recent call last):
      ..
    AssertionError: width must be a positive number of columns
    """
    assert width > 0, "width must be a positive number of columns"
    assert len(text) <= width, f"text '{text}' can't fit in {width} columns"
    if len(text) == width:  # if not special-cased, may say to write in column 1
        return 0
    return (width - len(text)) // 2 + 1


def decimalize_iterable(iterable):
    """
    Convert an iterable of some type of numbers to an iterable of Decimal.

    Raises TypeError or decimal.InvalidOperation if a value cannot be converted.

    Strings and integers work fine, and so do mixes:
        >>> decimalize_iterable([1, 2, 3, 4])
        [Decimal('1'), Decimal('2'), Decimal('3'), Decimal('4')]

        >>> decimalize_iterable(["6", "8.2", 10])
        [Decimal('6'), Decimal('8.2'), Decimal('10')]

    Doing it with floats is dangerous, so be careful what you ask for:
        >>> decimalize_iterable([1, 8, 2.6])  # doctest: +NORMALIZE_WHITESPACE
        [Decimal('1'), Decimal('8'),
         Decimal('2.600000000000000088817841970012523233890533447265625')]

    You can use things that are already Decimals too:
        >>> from decimal import Decimal; decimalize_iterable([Decimal("42")])
        [Decimal('42')]

    An empty list works fine:
        >>> decimalize_iterable([])
        []

    Unsupported types raise a TypeError:
        >>> decimalize_iterable([None])
        Traceback (most recent call last):
          ...
        TypeError: conversion from NoneType to Decimal is not supported

    But if you pass a bad string you get a different exception, because
    strings are a supported type but only if they contain valid data:
        >>> decimalize_iterable(["abc"])
        Traceback (most recent call last):
          ...
        decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
    """
    decimalized = []
    for stack_item in iterable:
        decimalized.append(decimal.Decimal(stack_item))
    return decimalized


def is_number(c):
    """
    Return True if the character /c/ can form part of a number in esc.
    Raise AssertionError if the string is not exactly one character.

    >>> is_number('0')
    True

    >>> is_number('5')
    True

    >>> is_number('.')
    True

    >>> is_number('a')
    False

    >>> is_number('168.3')
    Traceback (most recent call last):
      ...
    AssertionError: c must be a single character

    >>> is_number('')
    Traceback (most recent call last):
      ...
    AssertionError: c must be a single character
    """
    assert len(c) == 1, "c must be a single character"
    return ('0' <= c <= '9') or (c in ('.', '_', 'e'))


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

    return func(**{k: v for k, v in available_kwargs.items() if k in requested})


def partition(pred, iterable):
    """
    Use a predicate to partition entries into false entries and true entries.
    Itertools recipe from the standard library documentation.

    >>> [list(i) for i in partition(lambda i: i % 2 == 0, [1, 2, 3, 4, 5])]
    [[1, 3, 5], [2, 4]]

    >>> [list(i) for i in partition(lambda i: True, [1, 2, 3, 4, 5])]
    [[], [1, 2, 3, 4, 5]]
    """
    t1, t2 = itertools.tee(iterable)
    return itertools.filterfalse(pred, t1), filter(pred, t2)


def quit_if_screen_too_small(max_y, max_x):
    """
    If the terminal is too small, quit, providing a useful error message.
    """
    if max_y < REQUIRED_TERM_HEIGHT or max_x < REQUIRED_TERM_WIDTH:
        curses.endwin()
        sys.stderr.write(f"esc requires at least a "
                         f"{REQUIRED_TERM_WIDTH}x{REQUIRED_TERM_HEIGHT} terminal "
                         f"(this terminal is {max_x}x{max_y}).\n")
        sys.exit(1)


def truncate(string: str, max_length: int) -> str:
    """
    Truncate /string/ to at most /max_length/ using an ellipsis.
    max_length must be at least 3.

    >>> truncate("The quick brown fox jumps over the lazy dog.", 10)
    'The qui...'

    >>> truncate("I fit already.", 20)
    'I fit already.'

    >>> truncate("The quick brown fox jumps over the lazy dog.", 2)
    Traceback (most recent call last):
      ...
    AssertionError: max_length must be at least 3...
    """
    assert max_length > 3, \
        "max_length must be at least 3, as an ellipsis is 3 characters itself"
    if len(string) > max_length:
        string = string[:max_length - 3] + '...'
    return string
