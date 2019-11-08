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
    r"""
    Test case defined with the ``.ensure()`` attribute of functions
    decorated with :func:`@Operation <esc.commands.Operation>`.

    :param before:
        Required.
        A list of Decimals or values that can be coerced to Decimals.
        These values will be pushed onto a test stack
        that the operation will consume values from.
    :param after:
        Optional (either this or *raises* is required).
        A list of Decimals or values that can be coerced to Decimals.
        After the function is executed and changes the stack,
        the stack is compared to this list,
        and the test passes if they are identical.
    :param raises:
        Optional (either this or *after* is required).
        An exception type you expect the function to raise.
        This checks both the top-level exception type
        and any nested exceptions
        (since esc wraps many types of exceptions in
        :class:`FunctionExecutionError <esc.oops.FunctionExecutionError>`\ s).
        The test passes if executing the function
        (including all the machinery inside esc
        surrounding your actual function's execution,
        like pulling values off the stack)
        raises an exception of this type.
    :param close:
        If True, instead of doing an exact Decimal comparison,
        ``math.isclose()`` is used to perform a floating-point comparison.
        This is useful if dealing with irrational numbers
        or other sources of rounding error
        which may make it difficult
        to define the exact result in your test.

    Test cases are executed every time esc starts
    (this is not a performance issue in practice
    unless you have a *lot* of plugins).
    If a test ever fails,
    a :class:`ProgrammingError <esc.oops.ProgrammingError>` is raised.
    Preventing the whole program from starting may sound extreme,
    but wrong calculations are pretty bad news!

    Test cases are not inherently associated with an operation due to scope
    issues: Since the :class:`EscOperation <esc.commands.EscOperation>`
    itself is not returned to the functions file, only a decorated function,
    the function author can't access the :class:`EscOperation
    <esc.commands.EscOperation>`. Instead, they are associated with the
    function itself, and when the test() method is called on an
    :class:`EscOperation <esc.commands.EscOperation>`, it retrieves the test
    cases from the function and passes itself into the execute() method of
    each test case.
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

    def _oops_it(self, problem, operation):
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
        if self.after and self.raises:
            raise self._oops_it("included both 'after' and 'raises' clauses "
                                "(only one is allowed)", operation)

        try:
            start_dec = decimalize_iterable(self.before)
            if self.after is None:
                end_dec = []
            else:
                end_dec = decimalize_iterable(self.after)
        except (decimal.InvalidOperation, TypeError) as e:
            raise self._oops_it(
                "tried to place a non-decimal value on a test stack",
                operation) from e

        ss = StackState()
        registry = Registry()
        ss.push(start_dec)
        try:
            operation.execute(access_key=None, ss=ss, registry=registry)
        except Exception as e:
            if self.raises is None or not _recursive_exception_instance(e, self.raises):
                raise self._oops_it(
                    f"failed a self-test: {type(e).__name__} was raised and "
                    f"was not listed as the exception type "
                    f"in a raises parameter",
                    operation) from e
        else:
            if self.raises:
                raise self._oops_it(
                    f"failed a self-test: {self.raises.__name__} was not raised",
                    operation)
            elif not self._equal(ss.as_decimal(), end_dec):
                raise self._oops_it(
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
