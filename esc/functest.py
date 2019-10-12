"""
functest.py - rudimentary built-in unit testing for functions
"""

import decimal

from .oops import FunctionProgrammingError
from .stack import StackState
from .registers import Registry
from .util import decimalize_iterable


def _fpe(problem, operation, exception=None):
    return FunctionProgrammingError(function_name=operation.function.__name__,
                                    key=operation.key,
                                    description=operation.description,
                                    problem=problem,
                                    wrapped_exception=exception)


class TestCase:
    """
    Test case defined with function.ensure().

    Takes a "before" stack as input and either asserts that the operation
    completes successfully and the resulting stack is "after", or that the
    operation raises an exception of type "raises".

    Test cases are not inherently associated with an operation due to scope
    issues: Since the EscOperation itself is not returned to the functions
    file, only a decorated function, the function author can't access the
    EscOperation. Instead, they are associated with the function itself, and
    when the test() method is called on an EscOperation, it retrieves the
    test cases from the function and passes itself into the execute() method
    of each test case.
    """
    def __init__(self, before, after=None, raises=None):
        self.before = before
        self.after = after
        self.raises = raises

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
            raise _fpe("test case tried to place a non-decimal value on a test stack",
                       operation,
                       e)

        ss = StackState()
        registry = Registry()
        ss.push(start_dec)
        try:
            operation.execute(access_key=None, ss=ss, registry=registry)
        except Exception as e:
            if self.raises is None or not isinstance(e, self.raises):
                raise _fpe(
                    f"failed a self-test: {type(e).__name__} was raised and "
                    f"was not listed as the exception type "
                    f"in a raises parameter",
                    operation,
                    e)
        else:
            if self.raises:
                raise _fpe(f"failed a self-test: {self.raises.__name__} was not raised",
                           operation)
            elif ss.as_decimal() != end_dec:
                raise _fpe(
                    f"failed a self-test: Expected {end_dec}, "
                    f"but got {ss.s} as the final stack.",
                    operation)
