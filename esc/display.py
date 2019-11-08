"""
display.py - drive the curses interface

Other modules call into the EscScreen singleton defined here when they need
to update the screen.
"""

import curses
import itertools
import textwrap
from typing import Sequence

from .consts import (STACKDEPTH, STACKWIDTH, PROGRAM_NAME,
                     QUIT_CHARACTER, UNDO_CHARACTER, REDO_CHARACTER,
                     RETRIEVE_REG_CHARACTER, STORE_REG_CHARACTER, DELETE_REG_CHARACTER)
from .status import status
from .util import truncate, quit_if_screen_too_small, centered_position

_SCREEN = None


class Window:
    "One of the curses windows making up esc's interface."
    width = None
    height = None
    start_x = None
    start_y = None
    heading = None

    def __init__(self, scr):
        self.scr = scr
        self.window = curses.newwin(self.height, self.width, self.start_y, self.start_x)
        self.window.keypad(True)

    def _display_heading(self):
        if self.heading is not None:
            x_posn = centered_position(self.heading, self.width)
            self.window.addstr(0, x_posn, self.heading)

    def clear(self):
        """
        Hide this window from the screen. Call refresh() to put it back again.
        """
        if self.window is not None:
            self.window.clear()
            self.window.refresh()

    def refresh(self):
        if self.window is not None:
            self._display_heading()
            self.window.refresh()

    def getch(self):
        return self.window.getch()

    def putch(self, c):
        self.window.addstr(c)


class StatusWindow(Window):
    "Window for the status bar at the top of the screen."
    height = 1
    start_x = 0
    start_y = 0
    status_start = 16
    max_width = 79

    def __init__(self, scr, max_x):
        self.width = max_x
        super().__init__(scr)

        self.status_char = ' '
        self._status_msg = ''

        self.window.addstr(0, 0, (' ' * 79), curses.color_pair(1))
        self.window.addstr(0, 0, f"[{self.status_char}] {PROGRAM_NAME} |",
                           curses.color_pair(1))
        self.window.move(0, 1)
        self.refresh()

    @property
    def status_msg(self):
        return self._status_msg

    @status_msg.setter
    def status_msg(self, msg):
        self._status_msg = truncate(msg, self.max_width - self.status_start)

    def refresh(self):
        self.window.addstr(0, 1, self.status_char, curses.color_pair(1))
        self.window.addstr(0,
                           self.status_start,
                           ' ' * (self.max_width - self.status_start),
                           curses.color_pair(1))
        self.window.addstr(0, self.status_start, self.status_msg, curses.color_pair(1))
        super().refresh()

    def emplace_cursor(self):
        "Place the cursor in the status bar bracket."
        self.window.move(0, 1)

    def getch(self):
        self.emplace_cursor()
        return super().getch()



class StackWindow(Window):
    "Window for the stack, where the numbers go."
    width = 24
    height = 3 + STACKDEPTH
    start_x = 0
    start_y = 1
    heading = "Stack"

    def __init__(self, scr):
        super().__init__(scr)
        self.ss = None

        self.window.border()
        self.refresh()

    def refresh(self):
        self.window.clear()
        self.window.border()
        if self.ss:
            for index, stack_item in enumerate(self.ss):
                self.window.addstr(1 + index, 1, str(stack_item))
        super().refresh()

    def set_cursor_posn(self):
        """
        Place the cursor after the current character or on the next available
        line, as appropriate.
        """
        if self.ss.editing_last_item:
            self.window.move(1 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        else:
            # when not editing a number, cursor goes on *next line*
            self.window.move(2 + self.ss.stack_posn, self.ss.cursor_posn + 1)

    def backspace(self, bs_status):
        """
        Update the screen to show that a character was backspaced off the
        stack line being edited.
        """
        if bs_status == 0:  # character backspaced
            self.window.addstr(1 + self.ss.stack_posn, self.ss.cursor_posn + 1, ' ')
            self.window.move(1 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        elif bs_status == 1:  # stack item wiped out
            self.window.addstr(2 + self.ss.stack_posn, self.ss.cursor_posn + 1, ' ')
            self.window.move(2 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        else:  # nothing to backspace
            pass


class HistoryWindow(Window):
    "Window displaying a history of past actions."
    width = 32
    height = 3 + STACKDEPTH
    start_x = 24
    start_y = 1
    heading = "History"

    def __init__(self, scr):
        super().__init__(scr)
        self.operations = []
        self.refresh()

    def update_history(self, ss):
        self.operations = ss.operation_history[:]

    def refresh(self):
        self.window.clear()
        self.window.border()

        available_lines = self.height - 2
        visible_operations = self.operations[-available_lines:]
        for yposn, description in enumerate(visible_operations, 1):
            max_item_width = self.width - 2
            self.window.addstr(yposn, 1, truncate(description, max_item_width-3))

        super().refresh()


class CommandsWindow(Window):
    "Window displaying available commands/actions."
    width = 24
    start_x = 56
    start_y = 1
    heading = "Commands"

    border_width = 2  #: columns consumed by the window border
    key_width = 2     #: columns consumed by the menu char and space
    max_display_width = width - border_width - key_width

    def __init__(self, scr, max_y):
        self.height = max_y - 1
        super().__init__(scr)
        self.menu = None
        self.refresh()

    def refresh(self):
        self.window.clear()
        self.window.border()

        if self.menu is not None:
            min_xposn = 1
            max_xposn = 22
            xposn = min_xposn
            yposn = 1

            # Print menu title.
            if not self.menu.is_main_menu:
                self._add_menu(self.menu.description, yposn)
                if self.menu.mode_display:
                    self._add_mode_display(self.menu.mode_display(), yposn+1)
                yposn += 2

            # Print anonymous operations to the screen.
            for i in self.menu.anonymous_children:
                self._add_command(i.key, None, yposn, xposn)
                xposn += 2
                if xposn >= max_xposn - 2:
                    yposn += 1
                    xposn = min_xposn

            # Now normal operations and menus.
            yposn += 1
            xposn = min_xposn
            for i in self.menu.named_children:
                self._add_command(i.key, i.description, yposn, xposn)
                yposn += 1

            # then the special options, if on the main menu
            if self.menu.is_main_menu:
                self._add_command(STORE_REG_CHARACTER, 'store bos to reg', yposn, xposn)
                self._add_command(RETRIEVE_REG_CHARACTER, 'get bos from reg',
                                  yposn+1, xposn)
                self._add_command(DELETE_REG_CHARACTER, 'delete register',
                                  yposn+2, xposn)
                self._add_command(UNDO_CHARACTER, 'undo (', yposn+3, xposn)
                self._add_command(REDO_CHARACTER.lower(), 'redo)', yposn+3, xposn + 8)
                yposn += 4

            # then the quit option, which is always there but is not an operation
            quit_name = 'quit' if self.menu.is_main_menu else 'cancel'
            self._add_command(QUIT_CHARACTER, quit_name, yposn, xposn)

        # finally, make curses figure out how it's supposed to draw this
        super().refresh()

    def _add_menu(self, text, yposn):
        text = "(%s)" % text
        self._add_command('', text, yposn, centered_position(text, STACKWIDTH))

    def _add_mode_display(self, text, yposn):
        self._add_command('', text, yposn, centered_position(text, STACKWIDTH))

    def _add_command(self, char, descr, yposn, xposn):
        self.window.addstr(yposn, xposn, char, curses.color_pair(2))
        if descr:
            self.window.addstr(yposn,
                               xposn + 1 + len(char),
                               truncate(descr, self.max_display_width))


class RegistersWindow(Window):
    "Window displaying registers/variables currently defined."
    width = 56
    start_x = 0
    start_y = 4 + STACKDEPTH
    heading = "Registers"

    def __init__(self, scr, max_y):
        self.height = max_y - 1 - (3 + STACKDEPTH)
        self.register_pairs = []
        super().__init__(scr)
        self.refresh()

    def refresh(self):
        self.window.clear()
        self.window.border()

        for yposn, (register, stack_item) in enumerate(self.register_pairs, 1):
            assert len(register) == 1
            self.window.addstr(yposn, 1, register, curses.color_pair(2))
            self.window.addstr(yposn, 3, str(stack_item))

        super().refresh()

    def update_registry(self, registry):
        """
        Store the new register pairs to be used on a refresh().
        """
        self.register_pairs = registry.items()


class HelpWindow(Window):  # pylint: disable=too-many-instance-attributes
    "Temporary window displaying help messages."
    heading = "Help"

    # pylint: disable=too-many-arguments
    def __init__(self, scr, is_menu, help_title, signature_info, docstring,
                 results_info, max_y):
        self.height = max_y - 1
        if is_menu:
            self.width = StackWindow.width + HistoryWindow.width
            self.start_x = StackWindow.start_x
            self.start_y = StackWindow.start_y
        else:
            self.width = HistoryWindow.width + CommandsWindow.width
            self.start_x = HistoryWindow.start_x
            self.start_y = HistoryWindow.start_y

        super().__init__(scr)
        self.help_title = help_title
        self.signature_info = signature_info
        self.docstring = docstring
        self.results_info = results_info
        self.refresh()

    def refresh(self):
        self.scr.hide_registers_window()
        self.window.clear()
        self.window.border()
        self.window.addstr(self.start_y,
                           centered_position(self.help_title, self.width),
                           self.help_title,
                           curses.color_pair(2))

        indent = "    "
        docstring_lines = (indent + i for i in
                           textwrap.wrap(textwrap.dedent(self.docstring).strip(),
                                         self.width - 2 - len(indent)))

        if self.results_info is not None:
            rest = (
                "",
                "If you executed this command now...",
                *(f"    {i}" for i in self.results_info))
        else:
            rest = (())
        display_iterable = itertools.chain(
            ("Description:",),
            docstring_lines,
            ("", "Signature:"),
            self.signature_info,
            rest
        )
        for yposn, text in enumerate(display_iterable, self.start_y+1):
            self.window.addstr(yposn, 1, text)
            if yposn > self.height - 2:
                break
        super().refresh()


class EscScreen:
    """
    Facade bringing together display functions for all of the windows.
    """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.statusw = None
        self.stackw = None
        self.historyw = None
        self.commandsw = None
        self.registersw = None
        self.helpw = None
        self._setup()

    def _setup(self):
        """
        Initialize all the windows making up the esc interface,
        as well as curses settings.
        """
        max_y, max_x = self.stdscr.getmaxyx()
        quit_if_screen_too_small(max_y, max_x)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

        self.statusw = StatusWindow(self, max_x)
        self.stackw = StackWindow(self)
        self.historyw = HistoryWindow(self)
        self.commandsw = CommandsWindow(self, max_y)
        self.registersw = RegistersWindow(self, max_y)

    def refresh_all(self):
        self.refresh_status()
        for i in (self.stackw, self.historyw, self.commandsw, self.registersw):
            i.refresh()

    ### Status bar ###
    def focus_status_bar(self):
        "Place the cursor in the status bar bracket."
        self.statusw.emplace_cursor()

    def getch_status(self):
        return self.statusw.getch()

    def refresh_status(self):
        self.statusw.status_char = status.status_char
        self.statusw.status_msg = status.status_message
        self.statusw.refresh()


    ### Stack ###
    def refresh_stack(self, ss):
        self.stackw.ss = ss
        self.stackw.refresh()

    def place_cursor(self, ss):
        self.stackw.ss = ss
        self.stackw.set_cursor_posn()

    def backspace(self, ss, ss_return):
        self.stackw.ss = ss
        self.stackw.backspace(ss_return)

    def getch_stack(self):
        return self.stackw.getch()

    def putch_stack(self, c):
        self.stackw.putch(c)


    ### Commands ###
    def display_menu(self, menu):
        self.commandsw.menu = menu
        self.commandsw.refresh()


    ### Registers ###
    def update_registers(self, registry):
        self.registersw.update_registry(registry)
        self.registersw.refresh()

    def hide_registers_window(self):
        self.registersw.clear()


    ### History ###
    def update_history(self, ss):
        self.historyw.update_history(ss)
        self.historyw.refresh()


    ### Auxiliary windows ###
    # pylint: disable=too-many-arguments
    def show_help_window(self, is_menu: bool, help_title: str,
                         signature_info: Sequence[str], docstring: str,
                         results_info: Sequence[str]) -> None:
        "Display a help window for the command we requested."
        max_y, _ = self.stdscr.getmaxyx()
        self.helpw = HelpWindow(self, is_menu, help_title, signature_info,
                                docstring, results_info, max_y)


def screen():
    """
    It seems that if we don't define this as a function, we won't be able to
    access it with an import from another module because it won't have been
    defined at that time.
    """
    return _SCREEN


def fetch_input(in_menu) -> int:
    """
    Get one character of input, the location of the window to fetch from
    depending on whether we currently have a menu open (with a menu open, the
    cursor sits in the status bar). The character is returned as an int for
    compatibility with curses functions; use chr() to turn it into a string.
    """
    if in_menu:
        return screen().getch_status()
    else:
        return screen().getch_stack()


def init(stdscr):
    "Initialize the screen() from curses' stdscr."
    global _SCREEN
    _SCREEN = EscScreen(stdscr)
