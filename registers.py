"""
registers.py - manage registers
"""

from typing import Dict

from display import screen
from stack import StackItem


class Registry:
    def __init__(self):
        self.registers: Dict[str, StackItem] = {}
    
    def __getitem__(self, key):
        return self.registers[key]

    def __setitem__(self, key, value):
        self.registers[key] = value

    def items(self):
        return sorted(self.registers.items(), key=lambda i: i[0])