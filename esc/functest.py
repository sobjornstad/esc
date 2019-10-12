"""
functest.py - rudimentary built-in unit testing for functions
"""

import decimal
import math

from .oops import FunctionProgrammingError
from .stack import StackState
from .registers import Registry
from .util import decimalize_iterable


class TestCase:
    """
    Test case defined with function.ensure().

    Takes a "before" stack as input and either asserts that the operation
    completes successfully and the resulting stack is "after", or that the
    operation raises an exception of type "raises". "raises" also matches the
    types of *nested* exceptions; while this does slightly increase the risk
    of false positives, since esc will often wrap the exception actually
    generated in a generic error (e.g., FunctionExecutionError), this allows
    much more precise exception reasons to be checked.

    Test cases are not inherently associated with an operation due to scope
    issues: Since the EscOperation itself is not returned to the functions
    file, only a decorated function, the function author can't access the
    EscOperation. Instead, they are associated with the function itself, and
    when the test() method is called on an EscOperation, it retrieves the
    test cases from the function and passes itself into the execute() method
    of each test case.
    """
    def __init__(self, before, after=None, raises=None, close=False):
        self.before = before
        self.after = after
        self.raises = raises
        self.close = close

    def __repr__(self):
        if self.after:
            return f"<{self.before!r} --> {self.after!r}>"
        else:
            return f"<{self.before!r} ==> {self.raises.__name__}>"

    def _fpe(self, problem, operation):
        return FunctionProgrammingError(operation=operation,
                                        problem=f"under test {repr(self)} {problem}")

    def _equal(self, stack, expected):
        """
        Determine if results compare equal according to the definition of
        "equal" set out in the test definition.

        By default, this requires exact equality (including precision). This
        is typically nice for tests, as it can catch unexpected precision
        bugs. However, it can be problematic or even unusable in some cases,
        for instance when dealing with irrational numbers where the amount of
        precision in Decimal may be insufficient to ensure an exact match at
        the end of some operations. In this case you can set close=True on
        the test case and math.isclose() will be used instead. Note that this
        means your Decimals will be converted to floats first; this is
        unlikely to be a problem since we are already purposefully ignoring
        precision.
        """
        if self.close:
            return (len(stack) == len(expected)
                    and all(math.isclose(s, e) for s, e in zip(stack, expected)))
        else:
            return stack == expected

    def execute(self, operation):
        """
        Execute this test case against the EscOperation /operation/.
        Test cases raise an exception if they fail and otherwise do nothing.
        """
        try:
            start_dec = decimalize_iterable(self.before)
            if self.after is None:
                end_dec = []
            else:
                end_dec = decimalize_iterable(self.after)
        except (decimal.InvalidOperation, TypeError) as e:
            raise self._fpe(
                "test case tried to place a non-decimal value on a test stack",
                operation) from e

        ss = StackState()
        registry = Registry()
        ss.push(start_dec)
        try:
            operation.execute(access_key=None, ss=ss, registry=registry)
        except Exception as e:
            if self.raises is None or not _recursive_exception_instance(e, self.raises):
                raise self._fpe(
                    f"failed a self-test: {type(e).__name__} was raised and "
                    f"was not listed as the exception type "
                    f"in a raises parameter",
                    operation) from e
        else:
            if self.raises:
                raise self._fpe(
                    f"failed a self-test: {self.raises.__name__} was not raised",
                    operation)
            elif not self._equal(ss.as_decimal(), end_dec):
                raise self._fpe(
                    f"failed a self-test: Expected {end_dec}, "
                    f"but got {ss.as_decimal()} as the final stack",
                    operation)


def _recursive_exception_instance(exception, type_):
    """
    Determine if the exception or any of its nested exceptions are of the given type.
    """
    if isinstance(exception, type_):
        return True
    elif exception.__context__ is None:
        return False
    else:
        return _recursive_exception_instance(exception.__context__, type_)
