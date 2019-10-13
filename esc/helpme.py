"""
helpme.py - online help functions for esc
"""

import inspect

from . import builtin_stubs
from .display import screen, fetch_input
from .oops import NotInMenuError
from .status import status


def builtin_help(operation_key, menu):
    """
    Return an instance of the builtin class for the menu choice represented
    by operation_key, if one exists; otherwise return None.
    """
    if menu.is_main_menu:
        matching_builtin = [obj for name, obj in inspect.getmembers(builtin_stubs)
                            if inspect.isclass(obj)
                            and name != 'EscBuiltin'
                            and obj.key == operation_key]
        if matching_builtin:
            return matching_builtin[0]()
    return None


def get_help(operation_key, menu, ss, registry, recursing=False):
    """
    Display the on-line help page for the provided operation.
    """
    esc_function = builtin_help(operation_key, menu)
    if not esc_function:
        try:
            esc_function = menu.child(operation_key)
        except NotInMenuError as e:
            if not recursing:
                status.error(str(e))
            # When recursing, we get out of the menu by pressing a key
            # that doesn't exist.
            return

    screen().refresh_stack(ss)
    # For anonymous functions (those whose description is None),
    # use the key to describe the function.
    description = esc_function.description or esc_function.key
    if esc_function.is_menu:
        msg = f"Help: {description} (select a command or 'q' to return)"
    else:
        msg = f"Help: '{description}' (press any key to return)"
    status.advisory(msg)
    screen().refresh_status()
    screen().show_help_window(esc_function.is_menu,
                              esc_function.help_title,
                              esc_function.signature_info,
                              esc_function.__doc__,
                              esc_function.simulated_result(ss, registry))

    # If this is a menu, we can select items on the menu to dive into.
    if esc_function.is_menu:
        menu.execute(operation_key, ss, registry)
        screen().display_menu(esc_function)
        c = fetch_input(True)
        get_help(chr(c), esc_function, ss, registry, recursing=True)
    else:
        c = fetch_input(True)

    if not recursing:
        screen().helpw = None
