"""
oops.py - custom exceptions for esc
"""

import curses.ascii

class EscError(Exception):
    pass

class ProgrammingError(EscError):
    pass

class FunctionProgrammingError(ProgrammingError):
    """
    Programming error that occurs in a user's function (or, for that matter,
    a badly tested built-in function!).

    Wraps some handy logic for generating a standardized message.
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

class FunctionExecutionError(EscError):
    pass

class InvalidNameError(EscError):
    pass

class InsufficientItemsError(FunctionExecutionError):
    """
    Raised by functions that use pop=-1 to indicate not enough items are on
    the stack to finish their work.

    The function should raise an exception using the number_required
    constructor parameter. The menu will normally reraise the exception with
    a more useful message; a fallback message is provided in case this
    doesn't happen for some reason.
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
