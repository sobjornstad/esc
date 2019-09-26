"""
oops.py - custom exceptions for esc
"""

class EscError(Exception):
    pass

class ProgrammingError(EscError):
    pass

class NotInMenuError(EscError):
    pass

class FunctionExecutionError(EscError):
    pass

class InvalidNameError(EscError):
    pass

class InsufficientItemsError(EscError):
    """
    Raised by functions that use pop=-1 to indicate not enough items are on
    the stack to finish their work.
    """
    def __init__(self, number_required):
        self.number_required = number_required


class RollbackTransaction(Exception):
    def __init__(self, status_message=None):
        super().__init__()
        self.status_message = status_message

    def __str__(self):
        return f"<RollbackTransaction: message {self.status_message}>"