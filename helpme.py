"""
helpme.py - online help functions for esc
"""

from display import screen
from oops import NotInMenuError
import status


def get_help(operation_key, menu, ss):
    try:
        esc_function = menu.child(operation_key)
    except NotInMenuError as e:
        status.error(str(e))
        return

    screen().show_help_window(esc_function.help_title,
                              esc_function.signature_info,
                              esc_function.__doc__,
                              esc_function.simulated_result(ss))
