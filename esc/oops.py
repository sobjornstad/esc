"""
oops.py - custom exceptions for esc
"""

import curses.ascii

class EscError(Exception):
    "Base application exception for esc. Don't raise directly."


class ProgrammingError(EscError):
    """
    Indicates an error caused by incorrectly written or defined esc functions
    or other (possibly built-in ones). This includes modes, menus, and so on,
    as well as actual functions. It does not include runtime errors within
    functions themselves; these are FunctionExecutionErrors.
    """


class FunctionProgrammingError(ProgrammingError):
    """
    A more specific type of ProgrammingError that occurs when a user's
    @Function decorator or function parameters are invalid or function
    tests fail.

    The distinction is mostly for convenience within esc's codebase rather
    than because client code needs to tell the difference from other
    ProgrammingErrors; this class wraps some handy logic for generating a
    standardized message.
    """
    def __init__(self, function_name, key, description, problem,
                 wrapped_exception=None):
        super().__init__()
        self.function_name = function_name
        self.key = key
        self.description = description
        self.problem = problem
        self.wrapped_exception = wrapped_exception

        self.message = (f"The function '{self.function_name}' "
                        f"(key '{self.key}', description '{self.description}') "
                        f"{self.problem}. ")
        if self.wrapped_exception:
            self.message += ("The original error message is as follows:\n"
                             + repr(self.wrapped_exception))

    def __str__(self):
        return self.message


class NotInMenuError(EscError):
    """
    Raised when a keypress is parsed as a menu option but that key doesn't
    refer to any choice on the current menu. Describes the problem in a
    message that can be printed to the status bar.
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
    """
    A broad exception type that occurs when the code within a function
    couldn't be executed successfully for some reason. It is raised automatically
    when events like these happen:

    - a number is in the middle of being entered and isn't a valid number
    - a function performed an undefined operation like dividing by zero
    - a function raised FunctionExecutionError itself due to inability to
      complete the task
    - there are too many or too few items on the stack

    FunctionExecutionErrors normally result in the __str__ of the exception
    being printed to the status bar, so exception messages should be concise.

    A FunctionExecutionError may be raised directly, or one of its subclasses
    may be used.
    """

class InsufficientItemsError(FunctionExecutionError):
    """
    Raised directly by functions that use pop=-1 to indicate not enough items
    are on the stack to finish their work, or by the menu logic when a
    function requests /n/ pops and the stack contains fewer than /n/ items.

    Functions may use the simplified form of the exception, providing an int
    describing the number of items that should have been on the stack for the
    number_required constructor parameter. The menu will then reraise the
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
