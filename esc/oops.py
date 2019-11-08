"""
oops.py - custom exceptions for esc
"""

import curses.ascii

class EscError(Exception):
    "Base application exception for esc. Don't raise directly."


class ProgrammingError(EscError):
    r"""
    Indicates an error caused by incorrectly written or defined esc
    plugins. This includes modes, menus, operations, and so on.
    It does not include runtime errors within operation functions
    themselves; these are :class:`FunctionExecutionError`\ s.
    """


class FunctionProgrammingError(ProgrammingError):
    r"""
    A more specific type of :class:`ProgrammingError` that occurs when a
    user's :func:`@Operation <esc.commands.Operation>` decorator or function
    parameters are invalid or function tests fail.

    The distinction is mostly for convenience within esc's codebase rather
    than because client code needs to tell the difference from other
    :class:`ProgrammingError`\ s; this class wraps some handy logic for
    generating a standardized message.
    """
    def __init__(self, operation, problem):
        super().__init__()
        self.operation = operation
        self.function_name = self.operation.function.__name__
        self.key = self.operation.key
        self.description = self.operation.description
        self.problem = problem

        self.message = (f"The function '{self.function_name}' "
                        f"(key '{self.key}', description '{self.description}') "
                        f"{self.problem}. ")

    def __str__(self):
        return self.message


class NotInMenuError(EscError):
    """
    Raised when a keypress is parsed as a menu option or a menu's children
    are programmatically accessed by key, but the key doesn't refer to any
    choice on the current menu. Describes the problem in a message that can
    be printed to the status bar.
    """
    def __init__(self, access_key):
        super().__init__()
        specials = (' ', '\n', '\r', '\t')
        if ord(access_key) > 256 or access_key in specials:
            self.msg = "The key you pressed doesn't mean anything to esc here."
        else:
            self.msg = (f"There's no option '{curses.ascii.unctrl(access_key)}' "
                        f"in this menu.")

    def __str__(self):
        return self.msg


class InvalidNameError(EscError):
    """
    Raised when the user chooses an invalid name for a register or other label.
    """


class FunctionExecutionError(EscError):
    r"""
    A broad exception type that occurs when the code within an operation
    function couldn't be executed successfully for some reason. Examples
    include:

    - a number is in the middle of being entered and isn't a valid number
    - a function performed an undefined operation like dividing by zero
    - there are too many or too few items on the stack
    - a function directly raises this error due to invalid input
      or inability to complete its task for some other reason

    :class:`FunctionExecutionError`\ s normally result in the ``__str__`` of
    the exception being printed to the status bar, so exception messages
    should be concise.

    A :class:`FunctionExecutionError` may be raised directly, or one of its
    subclasses may be used.
    """

class InsufficientItemsError(FunctionExecutionError):
    """
    Raised directly by operations functions that request the entire stack to
    indicate not enough items are on the stack to finish their work, or by
    the menu logic when an operation requests more parameters than items on
    the stack.

    Functions may use the simplified form of the exception, providing an int
    describing the number of items that should have been on the stack for the
    ``number_required`` constructor parameter. esc will then reraise the
    exception with a more useful message; a fallback message is provided in
    case this doesn't happen for some reason.
    """
    def __init__(self, number_required, msg=None):
        super().__init__()
        self.number_required = number_required
        self.msg = msg

    def __str__(self):
        if self.msg:
            return self.msg
        else:
            return f"Insufficient items: needs at least {self.number_required}"


class RollbackTransaction(Exception):
    """
    Raised during a StackState .transaction() to indicate that the transaction
    should be rolled back due to an error. If status_message is provided, the
    status bar will be set to display the message.
    """
    def __init__(self, status_message=None):
        super().__init__()
        self.status_message = status_message

    def __str__(self):
        return f"<RollbackTransaction: message {self.status_message}>"
