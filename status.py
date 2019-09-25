"""
status.py - manage the status bar
"""

from enum import IntFlag

from display import screen


#TODO: This is bugly as an Enum. It looked nice and elegant at the start but
# gradually got worse and worse! We need to make it into a normal class
# containing a couple of state enums or bools.
class StatusState(IntFlag):
    """
    Calculator state for purpose of displaying a status.

    This is not a true flag; READY, ENTERING_NUMBER, and IN_MENU are mutually
    exclusive, as are ADVISORY and ERROR. Provided that only the state
    transition functions below are used, however, no other state can be
    obtained.

    We apparently have to use IntFlag so we can do a &= ~() to disable a flag
    iff it's on. Maybe I'm missing something.
    """
    READY = 1
    ENTERING_NUMBER = 2
    IN_MENU = 4
    EXPECTING_REGISTER = 8

    ADVISORY = 16
    ERROR = 32

    SEEN = 64


# pylint: disable=invalid-name
_STATE = StatusState.READY
_MSG = ""

def ready():
    "Clear errors and put calculator in a READY state."
    global _STATE
    _STATE = StatusState.READY

def entering_number():
    "Clear errors and put calculator in a state to enter a number."
    global _STATE
    _STATE = StatusState.ENTERING_NUMBER

def in_menu():
    "Clear errors and put calculator in a state to select from a menu."
    global _STATE
    # Preserve advisory or error markers;
    # these are more important than saying we're in a menu.
    _STATE &= (StatusState.ADVISORY | StatusState.ERROR)
    _STATE |= StatusState.IN_MENU

def expecting_register():
    "Clear errors and put calculator in a state to select a register."
    global _STATE
    _STATE = StatusState.EXPECTING_REGISTER

def advisory(msg):
    """
    Clear errors and display an advisory message in the status bar, without
    touching any other status icon set by the state.
    """
    global _STATE, _MSG
    _STATE &= ~StatusState.ERROR
    _STATE &= ~StatusState.SEEN
    _STATE |= StatusState.ADVISORY
    _MSG = msg

def error(msg):
    """
    Display an error icon and the provided message.
    """
    global _STATE, _MSG
    _STATE &= ~StatusState.ADVISORY
    _STATE &= ~StatusState.SEEN
    _STATE |= StatusState.ERROR
    _MSG = msg

def mark_seen():
    """
    We want to clear errors and advisories at the start of every time through
    the main loop so they go away as soon as the user starts doing something
    else, but if we did nothing else this would mean the user would never see
    any of them! Instead, we mark_seen() at this point. If the message hasn't
    been seen yet, we mark it as seen. If it has, then we get rid of it.
    """
    global _STATE
    if _STATE & StatusState.SEEN:
        _STATE &= ~StatusState.ADVISORY
        _STATE &= ~StatusState.ERROR
        _STATE &= ~StatusState.SEEN
    else:
        _STATE |= StatusState.SEEN


def redraw():
    """Redraw the status bar."""
    if _STATE & StatusState.READY:
        screen().set_status_char(' ')
        screen().set_status_msg('Ready')
    elif _STATE & StatusState.ENTERING_NUMBER:
        screen().set_status_char('i')
        screen().set_status_msg('Insert')
    elif _STATE & StatusState.IN_MENU:
        screen().set_status_char('m')
        screen().set_status_msg('Expecting menu selection')
    elif _STATE & StatusState.EXPECTING_REGISTER:
        screen().set_status_char('r')
        screen().set_status_msg('Expecting register identifier')

    if _STATE & StatusState.ERROR:
        screen().set_status_char('E')
        screen().set_status_msg(_MSG)
    elif _STATE & StatusState.ADVISORY:
        screen().set_status_msg(_MSG)
