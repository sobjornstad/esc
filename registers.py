"""
registers.py - manage registers
"""

from typing import Dict

from display import screen
from oops import InvalidNameError
from stack import StackItem


class Registry:
    def __init__(self):
        self.registers: Dict[str, StackItem] = {}

    def __contains__(self, value):
        return value in self.registers
    
    def __getitem__(self, key):
        return self.registers[key]

    def __setitem__(self, key, value):
        if not self._valid_name(key):
            raise InvalidNameError(
                "Register names must be uppercase or lowercase letters.")
        self.registers[key] = value

    @staticmethod
    def _valid_name(name: str):
        return len(name) == 1 and name.isalpha()

    def items(self):
        return sorted(self.registers.items(), key=lambda i: i[0])
