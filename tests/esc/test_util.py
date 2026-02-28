"""
Tests for util.py

The vast majority of the module's functions are pure and are tested via
convenient doctests. The few functions where that's ugly are tested here.
"""

import pytest

from esc.oops import ProgrammingError
from esc.util import magic_call, positional_caller


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


# === positional_caller tests ===

def _identity_bind(item, parm):
    "Trivial bind_item that returns the item unchanged."
    return item


class TestPositionalCaller:
    def test_basic_positional(self):
        def f(a, b):
            return a + b

        caller, num = positional_caller(f, _identity_bind, ())
        assert num == 2
        assert caller([10, 20], {}) == 30

    def test_positional_slices_from_end(self):
        "Two-param function gets the last two items from a longer list."
        def f(a, b):
            return (a, b)

        caller, num = positional_caller(f, _identity_bind, ())
        assert num == 2
        assert caller([1, 2, 3], {}) == (2, 3)

    def test_splat(self):
        def f(*args):
            return list(args)

        caller, num = positional_caller(f, _identity_bind, ())
        assert num == -1
        assert caller([1, 2, 3], {}) == [1, 2, 3]

    def test_special_kwargs(self):
        def f(a, *, registry):
            return (a, registry)

        caller, num = positional_caller(f, _identity_bind, ('registry',))
        assert num == 1
        result = caller([42], {'registry': 'REG'})
        assert result == (42, 'REG')

    def test_multiple_specials(self):
        def f(a, *, registry, testing):
            return (a, registry, testing)

        caller, num = positional_caller(
            f, _identity_bind, ('registry', 'testing'))
        assert num == 1
        result = caller([42], {'registry': 'R', 'testing': True})
        assert result == (42, 'R', True)

    def test_unused_special_not_passed(self):
        "A function that doesn't declare a special doesn't get it."
        def f(a):
            return a

        caller, _ = positional_caller(f, _identity_bind, ('registry',))
        assert caller([99], {'registry': 'REG'}) == 99

    def test_suffix_conversion(self):
        "bind_item is called with the parameter, enabling suffix-based conversion."
        def bind(item, parm):
            if parm.name.endswith('_str'):
                return str(item)
            return item

        def f(a, b_str):
            return (a, b_str)

        caller, num = positional_caller(f, bind, ())
        assert num == 2
        assert caller([10, 20], {}) == (10, '20')

    def test_no_params(self):
        def f():
            return 42

        caller, num = positional_caller(f, _identity_bind, ())
        assert num == 0
        assert caller([], {}) == 42

    def test_unknown_keyword_only_raises(self):
        "Keyword-only params not in special_names raise ProgrammingError."
        def f(a, *, unknown):
            pass

        with pytest.raises(ProgrammingError):
            positional_caller(f, _identity_bind, ('registry',))
