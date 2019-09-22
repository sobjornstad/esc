"""
modes.py - Manage calculator state/modes
"""


from dataclasses import dataclass
from typing import Any, Optional, Sequence

from oops import ProgrammingError


MODES = {}

@dataclass
class Mode:
    """
    esc modes implement basic calculator state like a degrees/radians switch.
    In esc, they are created and used by menus with families of related
    functions, where they can also be displayed. They have a name, a current
    value, and optionally a set of allowable values; if something ever causes
    the value to be set to a non-allowable value, a ProgrammingError will be
    raised, hopefully identifying the issue before it leads to wrong results.
    """
    name: str
    _value: Any
    allowable_values: Optional[Sequence[Any]]

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if self.allowable_values is not None and val not in self.allowable_values:
            raise ProgrammingError(f"Tried to set invalid mode {val} "
                                   f"(valid values: {','.join(self.allowable_values)})")
        self._value = val


def get(name):
    "Retrieve the value of a mode."
    try:
        return MODES[name].value
    except KeyError:
        return None


def register(name, default_value, allowable_values=None):
    "Create a new mode."
    if name in MODES:
        raise ProgrammingError("Tried to re-register an existing mode {name}.")
    MODES[name] = Mode(name, default_value, allowable_values)


#pylint: disable=redefined-builtin
def set(name, val):
    "Set a mode to a new value. Will raise ProgrammingError if mode is invalid."
    MODES[name].value = val
