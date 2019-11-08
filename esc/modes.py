"""
modes.py - Manage calculator state/modes
"""

from .oops import ProgrammingError

MODES = {}


class Mode:
    """
    esc modes implement basic calculator state like a degrees/radians switch.
    In esc, they are created and used by menus
    with families of related operations,
    where they can also be displayed.
    They have a name, a current value, and optionally a set of allowable values;
    if something ever causes the value to be set to a non-allowable value,
    a :class:`ProgrammingError <esc.oops.ProgrammingError>` will be raised,
    hopefully identifying the issue before it leads to wrong results.

    Modes are usually created by the :func:`esc.commands.Mode` factory function,
    not by calling this constructor directly.
    """
    def __init__(self, name, value, allowable_values):
        self.name = name
        self._value = value
        self.allowable_values = allowable_values

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
    """
    Retrieve the value of a mode with a given name. Return None if no mode by
    that name has been registered.
    """
    try:
        return MODES[name].value
    except KeyError:
        return None


def register(name, default_value, allowable_values=None):
    """
    Create a new mode. If the mode already exists,
    a :class:`ProgrammingError <esc.oops.ProgrammingError>` is raised.

    Modes should be registered by the :func:`esc.commands.Mode` factory function,
    not by calling this function directly.
    """
    if name in MODES:
        raise ProgrammingError("Tried to re-register an existing mode {name}.")
    MODES[name] = Mode(name, default_value, allowable_values)


#pylint: disable=redefined-builtin
def set(name, val):
    """
    Set a mode to a new value.
    If the mode doesn't exist, a ``KeyError`` will be raised.
    If the value is invalid for the mode,
    a :class:`ProgrammingError <esc.oops.ProgrammingError>` will be raised.
    """
    MODES[name].value = val
