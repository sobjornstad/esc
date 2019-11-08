"""
status.py - manage the status bar
"""

from contextlib import contextmanager
from enum import Enum, auto


class StatusState:
    """
    Describes the current status of the calculator.

    This includes the UI modality the calculator is in (not to be confused
    with *modes* configurable by plugins), such as "Ready", "Insert",
    waiting for a register, etc. It also includes information about whether
    an error just occurred and what information about said error should be
    displayed on the status bar.

    Most of esc will interact with this class by calling the methods, which
    transition the status into another state. The display functionality will
    read the properties status_char and status_message, which return the
    values that should be displayed on the status bar at any given time.
    """
    class Modality(Enum):
        """
        Describes the mode the calculator is in. A default status character
        and message is associated with each modality; this will be used unless
        overridden by an outstanding error or advisory.
        """
        READY = (' ', "Ready (<F1> for help)")
        ENTERING_NUMBER = ('i', "Insert")
        IN_MENU = ('m', "Expecting menu selection")
        EXPECTING_REGISTER = ('r', "Expecting register identifier (any letter)")
        EXPECTING_HELP = ('h', "Browsing help (select a command or menu)")

        def __init__(self, status_char, status_message):
            self.status_char = status_char
            self.status_message = status_message

    class SuccessCode(Enum):
        """
        Describes whether the last operation was OK or if an override message
        needs to be displayed. An error means something went wrong, an
        advisory might be used to inform the user that something happened
        successfully when that thing isn't obvious (for instance, a value was
        copied to the user's clipboard).
        """
        OK = auto()  # pylint: disable=invalid-name
        ADVISORY = auto()
        ERROR = auto()

    def __init__(self):
        self.state = StatusState.Modality.READY
        self.error_state = StatusState.SuccessCode.OK
        self.error_seen = True
        self.override_msg = ""
        self._saved_states = []

    def __repr__(self):
        if self.error_state == StatusState.SuccessCode.OK:
            err_str = "No Error"
        else:
            err_str = (f"Error {self.error_state} " +
                       ("(seen) :" if self.error_seen else "(not seen) :") +
                       f"message {self.override_msg})")
        return f"<StatusState: {self.state} - {err_str}>"

    @property
    def status_char(self):
        "The character we should be displaying in the status indicator box right now."
        if self.error_state == StatusState.SuccessCode.ERROR:
            return 'E'
        else:
            return self.state.status_char  # pylint: disable=no-member

    @property
    def status_message(self):
        "The status message we should be displaying right now."
        if self.error_state == StatusState.SuccessCode.OK:
            return self.state.status_message  # pylint: disable=no-member
        else:
            return self.override_msg

    def _clear_errors(self):
        self.error_state = StatusState.SuccessCode.OK

    def ready(self):
        "Clear errors and put calculator in a READY state."
        self.state = StatusState.Modality.READY
        self.error_state = StatusState.SuccessCode.OK
        self.error_seen = True

    def entering_number(self):
        self.state = StatusState.Modality.ENTERING_NUMBER

    def in_menu(self):
        self.state = StatusState.Modality.IN_MENU

    def expecting_register(self):
        "Clear errors and put calculator in a state to select a register."
        self._clear_errors()
        self.state = StatusState.Modality.EXPECTING_REGISTER

    def expecting_help(self):
        "Clear errors and put calculator in a state to select a command to get help on."
        self._clear_errors()
        self.state = StatusState.Modality.EXPECTING_HELP

    def advisory(self, msg):
        """
        Clear errors and display an advisory message in the status bar, without
        touching any other status icon set by the state.
        """
        self.error_state = StatusState.SuccessCode.ADVISORY
        self.error_seen = False
        self.override_msg = msg

    def error(self, msg):
        """
        Display an error icon and the provided message.
        """
        self.error_state = StatusState.SuccessCode.ERROR
        self.error_seen = False
        self.override_msg = msg

    def mark_seen(self):
        """
        We want to clear errors and advisories at the start of every time through
        the main loop so they go away as soon as the user starts doing something
        else, but if we did nothing else this would mean the user would never see
        any of them! Instead, we mark_seen() at this point. If the message hasn't
        been seen yet, we mark it as seen. If it has, then we get rid of it.
        """
        if self.error_seen:
            self._clear_errors()
        else:
            self.error_seen = True

    def push_state(self):
        """
        Save the current state onto a stack for later restoration.
        """
        self._saved_states.append((self.state,
                                   self.error_state,
                                   self.error_seen,
                                   self.override_msg))

    def pop_state(self):
        """
        Restore the most recently pushed state.
        """
        self.state, self.error_state, self.error_seen, self.override_msg = \
            self._saved_states.pop()

    @contextmanager
    def save_state(self):
        """
        Save the current status while performing some operation.
        """
        self.push_state()
        try:
            yield
        finally:
            self.pop_state()


# pylint: disable=invalid-name
status = StatusState()
