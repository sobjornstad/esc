"""
Tests for util.py

The vast majority of the module's functions are pure and are tested via
convenient doctests. The few functions where that's ugly are tested here.
"""

import pytest

from esc.oops import ProgrammingError
from esc.util import magic_call


def test_magic_call():
    """
    We can magic-call a function with more arguments than it needs,
    and the order doesn't matter.
    """
    def f(y, x):
        return x - y

    kwargs = {'x': 2, 'y': 3, 'z': 8}
    assert magic_call(f, kwargs) == -1


def test_magic_call_missing_args():
    "However, the function can't request arguments we don't have."
    def f(x, y):
        return x + y

    kwargs = {'x': 2}
    with pytest.raises(ProgrammingError) as excinfo:
        magic_call(f, kwargs)
    assert ('requested the following arguments which are not available'
            in str(excinfo.value))
