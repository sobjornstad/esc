"""
display.py - drive the curses interface

Other modules call into the EscScreen singleton defined here when they need
to update the screen.
"""

from contextlib import contextmanager
import curses
import itertools
import textwrap
from typing import Sequence

from consts import STACKDEPTH, STACKWIDTH, PROGRAM_NAME
from util import truncate, quit_if_screen_too_small, centered_position

# pylint: disable=invalid-name
_screen = None


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
    max_width = 80

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
        self.window.addstr(0, self.status_start, ' ' * (79 - 15), curses.color_pair(1))
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

    def backspace(self, status):
        """
        Update the screen to show that a character was backspaced off the
        stack line being edited.
        """
        if status == 0:  # character backspaced
            self.window.addstr(1 + self.ss.stack_posn, self.ss.cursor_posn + 1, ' ')
            self.window.move(1 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        elif status == 1:  # stack item wiped out
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

    def __init__(self, scr, max_y):
        self.height = max_y - 1
        super().__init__(scr)
        self.commands = []
        self.refresh()

    def refresh(self):
        self.window.clear()
        self.window.border()

        # TODO: This is desperately ugly and is intended to be a hack until
        # commands are objects we can introspect.
        border_width = 2
        key_width = 2
        max_width = self.width - border_width - key_width
        for command in self.commands:
            try:
                self.window.addstr(*command[:-1])
                if command[-1]:
                    self.window.addstr(command[0],
                                       command[1] + 1 + len(command[2]),
                                       truncate(command[-1], max_width))
            except curses.error:
                pass
        super().refresh()

    def add_menu(self, text, yposn):
        text = "(%s)" % text
        self.add_command('', text, yposn, centered_position(text, STACKWIDTH))

    def add_mode_display(self, text, yposn):
        self.add_command('', text, yposn, centered_position(text, STACKWIDTH))

    def add_command(self, char, descr, yposn, xposn):
        self.commands.append((yposn, xposn, char, curses.color_pair(2), descr))

    def reset(self):
        self.commands.clear()


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
        self.register_pairs = list(registry.items())


class HelpWindow(Window):
    "Temporary window displaying help messages."
    heading = "Help"

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
        for i in (self.statusw, self.stackw, self.historyw, self.commandsw,
                  self.registersw):
            i.refresh()

    ### Status bar ###
    def set_status_char(self, c):
        """Place the indicated character /c/ in the status bracket."""
        self.statusw.status_char = c
        self.statusw.refresh()

    def set_status_msg(self, msg):
        self.statusw.status_msg = msg
        self.statusw.refresh()

    def focus_status_bar(self):
        "Place the cursor in the status bar bracket."
        self.statusw.emplace_cursor()

    def getch_status(self):
        return self.statusw.getch()


    ### Stack ###
    def refresh_stack(self, ss):
        self.stackw.ss = ss
        self.stackw.refresh()

    def place_cursor(self, ss):
        self.stackw.ss = ss
        self.stackw.set_cursor_posn()

    def backspace(self, ss, ssReturn):
        self.stackw.ss = ss
        self.stackw.backspace(ssReturn)

    def getch_stack(self):
        return self.stackw.getch()

    def putch_stack(self, c):
        self.stackw.putch(c)


    ### Commands ###
    def add_menu(self, text, yposn):
        self.commandsw.add_menu(text, yposn)

    def add_mode_display(self, text, yposn):
        self.commandsw.add_mode_display(text, yposn)

    def add_command(self, char, descr, yposn, xposn):
        self.commandsw.add_command(char, descr, yposn, xposn)

    def reset_commands_window(self):
        self.commandsw.reset()


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
    def show_help_window(self, is_menu: bool, help_title: str,
                         signature_info: Sequence[str], docstring: str,
                         results_info: Sequence[str]) -> None:
        max_y, _ = self.stdscr.getmaxyx()
        self.helpw = HelpWindow(self, is_menu, help_title, signature_info,
                                docstring, results_info, max_y)


def screen():
    """
    It seems that if we don't define this as a function, we won't be able to
    access it with an import from another module because it won't have been
    defined at that time.
    """
    return _screen


def init(stdscr):
    "Initialize the screen() from curses' stdscr."
    global _screen
    _screen = EscScreen(stdscr)
