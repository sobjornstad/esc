"""
helpme.py - online help functions for esc
"""

import curses
from display import screen
from textwrap import dedent


def get_help(operation_key, menu, ss):
    help_text = dedent("""
    Your mother called and told me to use this function.

    It's an example of how you do it.
    """)

    screen().show_help_window(help_text)
