"""
helpme.py - online help functions for esc
"""

import curses
import inspect

from . import builtin_stubs
from .display import screen, fetch_input
from .oops import NotInMenuError
from .status import status


def _fetch_input_handling_resize(redraw):
    """Fetch input from the status bar, handling terminal resizes."""
    while True:
        c = fetch_input(True)
        if c == curses.KEY_RESIZE:
            screen().handle_resize()
            if not screen().too_small:
                redraw()
            continue
        return c


def _show_help(esc_command, ss, registry):
    """Render the help display for the given command."""
    screen().refresh_stack(ss)
    status.advisory(status_message(esc_command))
    screen().refresh_status()
    screen().show_help_window(esc_command.is_menu,
                              esc_command.help_title,
                              esc_command.signature_info,
                              esc_command.__doc__,
                              esc_command.simulated_result(ss, registry))


def builtin_help(operation_key, menu):
    """
    Return an instance of the builtin class for the menu choice represented
    by operation_key, if one exists; otherwise return None.

    >>> from esc.commands import main_menu
    >>> builtin_help('q', main_menu)
    <esc.builtin_stubs.Quit object at ...>

    >>> undoer = builtin_help('u', main_menu)
    >>> undoer.key
    'u'
    >>> undoer.description
    'undo'
    >>> undoer.simulated_result(None, None)
    ('The last change made to your stack (if any)', 'would be undone.')
    """
    if menu.is_main_menu:
        matching_builtin = [obj for name, obj in inspect.getmembers(builtin_stubs)
                            if inspect.isclass(obj)
                            and name != 'EscBuiltin'
                            and obj.key == operation_key]
        if matching_builtin:
            return matching_builtin[0]()
    return None


def status_message(command):
    """
    Determine the status message to use to describe the command we're looking
    at.
    """
    # For anonymous operations (those whose description is None),
    # use the key to describe the command.
    description = command.description or command.key
    if command.is_menu:
        return f"Help: {description} (select a command or 'q' to return)"
    else:
        return f"Help: '{description}' (press any key to return)"


def get_help(operation_key, menu, ss, registry, recursing=False):
    """
    Display the on-line help page for the provided operation.
    """
    esc_command = builtin_help(operation_key, menu)
    if not esc_command:
        try:
            esc_command = menu.child(operation_key)
        except NotInMenuError as e:
            if not recursing:
                status.error(str(e))
            # When recursing, we get out of the menu by pressing a key
            # that doesn't exist.
            return

    _show_help(esc_command, ss, registry)

    # If this is a menu, we can select items on the menu to dive into.
    if esc_command.is_menu:
        menu.execute(operation_key, ss, registry)
        screen().display_menu(esc_command)

        def redraw():
            _show_help(esc_command, ss, registry)
            screen().display_menu(esc_command)

        c = _fetch_input_handling_resize(redraw)
        get_help(chr(c), esc_command, ss, registry, recursing=True)
    else:
        c = _fetch_input_handling_resize(
            lambda: _show_help(esc_command, ss, registry))

    if not recursing:
        screen().helpw = None
