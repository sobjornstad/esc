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