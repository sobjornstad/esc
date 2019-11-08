"""
Tests for the on-line help system.
"""

from decimal import Decimal
import pytest

from esc import builtin_stubs
from esc import display
from esc import helpme
from esc.status import status
from esc.commands import main_menu
from esc.registers import Registry
from esc.stack import StackState


# pylint: disable=redefined-outer-name


def test_status_message_anonymous():
    """
    Anonymous functions should use their key as a status description.
    """
    add_func = main_menu.child('+')
    assert helpme.status_message(add_func) == "Help: '+' (press any key to return)"


def test_status_message_nonanonymous():
    "Named functions should use their description instead."
    exchange_func = main_menu.child('x')
    assert (helpme.status_message(exchange_func) ==
            "Help: 'exchange bos, sos' (press any key to return)")


def test_status_message_builtin():
    "Builtins have a description."
    quit_func = builtin_stubs.Quit()
    assert helpme.status_message(quit_func) == "Help: 'quit' (press any key to return)"


class MockScreen:
    "Mock for screen()."
    helpw = None
    called = set()

    def getch_status(self):
        self.called.add('getch_status')
        return ord('q')  # get back out of help

    def refresh_stack(self, ss):
        self.called.add('refresh_stack')

    def refresh_status(self):
        self.called.add('refresh_status')

    def show_help_window(self,
                         is_menu,
                         help_title,
                         signature_info,
                         doc,
                         simulated_result):
        self.called.add('show_help_window')

    def display_menu(self, command):
        self.called.add('display_menu')

    def mock_screen(self):
        """
        Fast way to create a callable that can return a singleton-ish
        thing, to monkey-patch the global screen() object.
        """
        return self


@pytest.fixture
def help_test_case(monkeypatch):
    "Set up environment for a get_help() test case."
    ss = StackState()
    ss.push((Decimal(2), Decimal(3)))
    registry = Registry()
    mock_screen = MockScreen()
    monkeypatch.setattr(helpme, 'screen', mock_screen.mock_screen)
    monkeypatch.setattr(display, 'screen', mock_screen.mock_screen)
    return ss, registry, mock_screen


default_call_set = {
    'getch_status',
    'refresh_stack',
    'refresh_status',
    'show_help_window',
}


def test_get_help_simple(help_test_case):
    "We can get help on a simple (non-menu) function."
    ss, registry, mock_screen = help_test_case
    helpme.get_help('+', main_menu, ss, registry)
    assert mock_screen.called == default_call_set


def test_get_help_menu_item(help_test_case):
    "We can get help on a function in a menu."
    ss, registry, mock_screen = help_test_case
    constants_menu = main_menu.child('i')
    helpme.get_help('p', constants_menu, ss, registry)
    assert mock_screen.called == default_call_set


def test_get_help_menu(help_test_case):
    "We can get help on a menu itself."
    ss, registry, mock_screen = help_test_case
    helpme.get_help('i', main_menu, ss, registry)
    assert mock_screen.called == default_call_set.union({'display_menu'})

def test_get_help_invalid_key(help_test_case, monkeypatch):
    """
    An error message is printed to the status bar when we ask for help on a
    nonexistent menu item.
    """
    ss, registry, mock_screen = help_test_case
    the_error = None
    def my_error(msg):
        nonlocal the_error
        the_error = msg
    monkeypatch.setattr(status, 'error', my_error)
    helpme.get_help('Q', main_menu, ss, registry)
    assert the_error == "There's no option 'Q' in this menu."
