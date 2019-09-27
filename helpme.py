"""
helpme.py - online help functions for esc
"""

from display import screen
import menus
from oops import NotInMenuError
import status
import util


def get_help(operation_key, menu, ss, recursing=False):
    """
    Display the on-line help page for the provided operation.
    """
    try:
        esc_function = menu.child(operation_key)
    except NotInMenuError as e:
        if not recursing:
            status.error(str(e))
        # When recursing, we get out of the menu by pressing a key that doesn't exist.
        return

    screen().refresh_stack(ss)
    if esc_function.is_menu:
        msg = f"Help: {esc_function.description} (select a command or 'q' to return)"
    else:
        msg = f"Help: '{esc_function.description}' (press any key to return)"
    status.advisory(msg)
    status.redraw()
    screen().show_help_window(esc_function.is_menu,
                              esc_function.help_title,
                              esc_function.signature_info,
                              esc_function.__doc__,
                              esc_function.simulated_result(ss))

    # If this is a menu, we can select items on the menu to dive into.
    if esc_function.is_menu:
        menu.execute(operation_key, ss)
        menus.display_menu(esc_function)
        c = util.fetch_input(True)
        get_help(chr(c), esc_function, ss, recursing=True)
    else:
        c = util.fetch_input(True)

    if not recursing:
        screen().helpw = None
        screen().refresh_all()
        status.ready()
