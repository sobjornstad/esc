"""
registers.py - manage registers
"""

from typing import Dict

from .oops import InvalidNameError
from .stack import StackItem


class Registry:
    """
    The Registry stores the values of esc registers. It's basically a fancy
    dictionary with some validation and a display-sorted items() method.
    """
    def __init__(self):
        self._registers: Dict[str, StackItem] = {}

    def __contains__(self, value):
        return value in self._registers

    def __len__(self):
        return len(self._registers)

    def __getitem__(self, key):
        return self._registers[key]

    def __setitem__(self, key, value):
        if not self._valid_name(key):
            raise InvalidNameError(
                "Register names must be uppercase or lowercase letters.")
        self._registers[key] = value

    def __delitem__(self, key):
        del self._registers[key]

    @staticmethod
    def _valid_name(name: str):
        return len(name) == 1 and name.isalpha()

    def items(self):
        return sorted(self._registers.items(), key=lambda i: i[0])

    def values(self):
        return self._registers.values()
