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


class RollbackTransaction(Exception):
    def __init__(self, status_message=None):
        super().__init__()
        self.status_message = status_message

    def __str__(self):
        return f"<RollbackTransaction: message {self.status_message}>"