"""
display.py - drive the curses interface

Other modules call into the EscScreen singleton defined here when they need
to update the screen.
"""

import curses
import itertools
import math
import textwrap
from typing import Sequence

from .consts import (PROGRAM_NAME,
                     QUIT_CHARACTER, UNDO_CHARACTER, REDO_CHARACTER,
                     RETRIEVE_REG_CHARACTER, STORE_REG_CHARACTER,
                     DELETE_REG_CHARACTER, UNIT_ENTRY_CHARACTER)
from .layout import compute_layout, MIN_TERM_WIDTH, MIN_TERM_HEIGHT
from .status import status
from .util import truncate, centered_position

_SCREEN = None


class Window:
    "One of the curses windows making up esc's interface."
    heading = None

    def __init__(self, scr, width, height, start_x, start_y):
        self.scr = scr
        self.width = width
        self.height = height
        self.start_x = start_x
        self.start_y = start_y
        self.window = curses.newwin(height, width, start_y, start_x)
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

    def __init__(self, scr, spec):
        super().__init__(scr, spec.width, spec.height, spec.x, spec.y)
        self.max_width = self.width - 1
        self.status_start = len(f"[ ] {PROGRAM_NAME} | ")

        self.status_char = ' '
        self._status_msg = ''

        try:
            self.window.addstr(
                0, 0, (' ' * self.max_width), curses.color_pair(1))
            self.window.addstr(
                0, 0, f"[{self.status_char}] {PROGRAM_NAME} |",
                curses.color_pair(1))
            self.window.move(0, 1)
        except curses.error:
            pass
        self.refresh()

    @property
    def status_msg(self):
        return self._status_msg

    @status_msg.setter
    def status_msg(self, msg):
        self._status_msg = truncate(msg, self.max_width - self.status_start)

    def refresh(self):
        try:
            self.window.addstr(0, 1, self.status_char, curses.color_pair(1))
            self.window.addstr(0,
                               self.status_start,
                               ' ' * (self.max_width - self.status_start),
                               curses.color_pair(1))
            self.window.addstr(0, self.status_start, self.status_msg,
                               curses.color_pair(1))
        except curses.error:
            pass
        super().refresh()

    def emplace_cursor(self):
        "Place the cursor in the status bar bracket."
        self.window.move(0, 1)

    def getch(self):
        self.emplace_cursor()
        return super().getch()


class StackWindow(Window):
    "Window for the stack, where the numbers go."
    heading = "Stack"

    def __init__(self, scr, spec):
        super().__init__(scr, spec.width, spec.height, spec.x, spec.y)
        self.ss = None
        self._scroll_offset = 0
        self.partial_unit = None  # None = not in unit mode; "" = unit mode, empty buffer

        self.window.border()
        self.refresh()

    def refresh(self):
        try:
            self.window.clear()
            self.window.border()
            if self.ss:
                visible_slots = self.height - 3
                items = list(self.ss)
                visible_items = items[-visible_slots:]
                self._scroll_offset = max(0, len(items) - visible_slots)
                max_text_width = self.width - 2
                last_index = len(visible_items) - 1
                for index, stack_item in enumerate(visible_items):
                    num_str = truncate(stack_item.string, max_text_width)
                    self.window.addstr(1 + index, 1, num_str)

                    # For bos during unit entry, show partial_unit
                    if self.partial_unit is not None and index == last_index:
                        unit_str = " " + self.partial_unit
                        col = 1 + len(num_str)
                        remaining = max_text_width - len(num_str)
                        if remaining > 1:
                            unit_str = truncate(
                                unit_str, remaining
                            ) if len(unit_str) > remaining else unit_str
                            self.window.addstr(
                                1 + index, col, unit_str,
                                curses.color_pair(3))
                    elif (stack_item.unit is not None
                            and not stack_item.unit.is_unitless):
                        unit_str = " " + stack_item.unit.display()
                        col = 1 + len(num_str)
                        remaining = max_text_width - len(num_str)
                        if remaining > 1:
                            unit_str = truncate(
                                unit_str, remaining
                            ) if len(unit_str) > remaining else unit_str
                            self.window.addstr(
                                1 + index, col, unit_str,
                                curses.color_pair(3))
        except curses.error:
            pass
        super().refresh()

    def _display_row(self, stack_posn):
        """
        Map an absolute stack position to a display row in the window,
        using the scroll offset from the last refresh() so that row
        numbers stay consistent with what is actually on screen.
        """
        return 1 + stack_posn - self._scroll_offset

    def set_cursor_posn(self):
        """
        Place the cursor after the current character or on the next available
        line, as appropriate.
        """
        try:
            if self.partial_unit is not None:
                # During unit entry, cursor sits after the partial unit on BOS row
                row = self._display_row(self.ss.stack_posn)
                row = max(1, min(row, self.height - 2))
                bos_str = self.ss.bos.string if not self.ss.is_empty else ""
                col = 1 + len(bos_str) + len(" ") + len(self.partial_unit)
                col = min(col, self.width - 2)
                self.window.move(row, col)
            elif self.ss.editing_last_item:
                row = self._display_row(self.ss.stack_posn)
                row = max(1, min(row, self.height - 2))
                self.window.move(row, self.ss.cursor_posn + 1)
            else:
                # when not editing a number, cursor goes on *next line*
                row = self._display_row(self.ss.stack_posn) + 1
                row = max(1, min(row, self.height - 2))
                self.window.move(row, self.ss.cursor_posn + 1)
        except curses.error:
            pass

    def backspace(self, bs_status):
        """
        Update the screen to show that a character was backspaced off the
        stack line being edited.
        """
        try:
            if bs_status == 0:  # character backspaced
                row = self._display_row(self.ss.stack_posn)
                self.window.addstr(row, self.ss.cursor_posn + 1, ' ')
                self.window.move(row, self.ss.cursor_posn + 1)
            elif bs_status == 1:  # stack item wiped out
                row = self._display_row(self.ss.stack_posn) + 1
                self.window.addstr(row, self.ss.cursor_posn + 1, ' ')
                self.window.move(row, self.ss.cursor_posn + 1)
            else:  # nothing to backspace
                pass
        except curses.error:
            pass


class HistoryWindow(Window):
    "Window displaying a history of past actions."
    heading = "History"

    def __init__(self, scr, spec):
        super().__init__(scr, spec.width, spec.height, spec.x, spec.y)
        self.operations = []
        self.refresh()

    def update_history(self, ss):
        self.operations = ss.operation_history[:]

    def refresh(self):
        try:
            self.window.clear()
            self.window.border()

            available_lines = self.height - 2
            visible_operations = self.operations[-available_lines:]
            for yposn, description in enumerate(visible_operations, 1):
                max_item_width = self.width - 2
                self.window.addstr(
                    yposn, 1, truncate(description, max_item_width - 3))
        except curses.error:
            pass

        super().refresh()


class CommandsWindow(Window):
    "Window displaying available commands/actions."
    heading = "Commands"

    border_width = 2  #: columns consumed by the window border
    key_width = 2     #: columns consumed by the menu char and space

    def __init__(self, scr, spec):
        super().__init__(scr, spec.width, spec.height, spec.x, spec.y)
        self.max_display_width = self.width - self.border_width - self.key_width
        self.menu = None
        self.refresh()

    def refresh(self):
        try:
            self.window.clear()
            self.window.border()

            if self.menu is not None:
                min_xposn = 1
                max_xposn = self.width - 2
                xposn = min_xposn
                yposn = 1
                truncated = False

                # Print menu title.
                if not self.menu.is_main_menu:
                    self._add_menu(self.menu.description, yposn)
                    if self.menu.mode_display:
                        self._add_mode_display(
                            self.menu.mode_display(), yposn+1)
                    yposn += 2

                # Print anonymous operations to the screen.
                for i in self.menu.anonymous_children:
                    if yposn >= self.height - 1:
                        truncated = True
                        break
                    self._add_command(i.key, None, yposn, xposn)
                    xposn += 2
                    if xposn >= max_xposn - 2:
                        yposn += 1
                        xposn = min_xposn

                # Now normal operations and menus.
                yposn += 1
                xposn = min_xposn
                for i in self.menu.named_children:
                    if yposn >= self.height - 1:
                        truncated = True
                        break
                    self._add_command(i.key, i.description, yposn, xposn)
                    yposn += 1

                # then the special options, if on the main menu
                if self.menu.is_main_menu:
                    if yposn < self.height - 1:
                        self._add_command(STORE_REG_CHARACTER,
                                          'store bos to reg', yposn, xposn)
                    else:
                        truncated = True
                    if yposn + 1 < self.height - 1:
                        self._add_command(RETRIEVE_REG_CHARACTER,
                                          'get bos from reg', yposn+1, xposn)
                    else:
                        truncated = True
                    if yposn + 2 < self.height - 1:
                        self._add_command(DELETE_REG_CHARACTER,
                                          'delete register', yposn+2, xposn)
                    else:
                        truncated = True
                    if yposn + 3 < self.height - 1:
                        self._add_command(UNDO_CHARACTER,
                                          'undo (', yposn+3, xposn)
                        redo_x = min(xposn + 8, max_xposn - 6)
                        self._add_command(REDO_CHARACTER.lower(),
                                          'redo)', yposn+3, redo_x)
                    else:
                        truncated = True
                    if yposn + 4 < self.height - 1:
                        self._add_command(UNIT_ENTRY_CHARACTER,
                                          'add unit tag', yposn+4, xposn)
                    else:
                        truncated = True
                    yposn += 5

                # then the quit option, which is always there but not an op
                if yposn < self.height - 1:
                    quit_name = ('quit' if self.menu.is_main_menu
                                 else 'cancel')
                    self._add_command(
                        QUIT_CHARACTER, quit_name, yposn, xposn)
                else:
                    truncated = True

                if truncated:
                    fill = " " * max(0, self.width - 5)
                    self.window.addstr(self.height - 2, 1, "..." + fill)
        except curses.error:
            pass

        # finally, make curses figure out how it's supposed to draw this
        super().refresh()

    def _add_menu(self, text, yposn):
        text = "(%s)" % text
        self._add_command(
            '', text, yposn, centered_position(text, self.width - 2))

    def _add_mode_display(self, text, yposn):
        self._add_command(
            '', text, yposn, centered_position(text, self.width - 2))

    def _add_command(self, char, descr, yposn, xposn):
        self.window.addstr(yposn, xposn, char, curses.color_pair(2))
        if descr:
            self.window.addstr(yposn,
                               xposn + 1 + len(char),
                               truncate(descr, self.max_display_width))


class RegistersWindow(Window):
    "Window displaying registers/variables currently defined."
    heading = "Registers"

    def __init__(self, scr, spec):
        super().__init__(scr, spec.width, spec.height, spec.x, spec.y)
        self.register_pairs = []
        self.refresh()

    def refresh(self):
        try:
            self.window.clear()
            self.window.border()

            pairs = list(self.register_pairs)
            rows_available = self.height - 2
            min_col_width = 8

            if len(pairs) <= rows_available:
                num_cols = 1
            else:
                num_cols = math.ceil(len(pairs) / rows_available)
                max_cols = max(1, (self.width - 2) // min_col_width)
                num_cols = min(num_cols, max_cols)

            col_width = (self.width - 2) // num_cols
            total_slots = num_cols * rows_available
            truncated = len(pairs) > total_slots

            for idx, (register, stack_item) in enumerate(pairs):
                if idx >= total_slots:
                    break
                col = idx // rows_available
                row = idx % rows_available
                x_offset = col * col_width + 1
                assert len(register) == 1
                self.window.addstr(row + 1, x_offset,
                                   register, curses.color_pair(2))
                value_width = col_width - 3
                if value_width > 3:
                    num_str = truncate(stack_item.string, value_width)
                    self.window.addstr(row + 1, x_offset + 2, num_str)
                    # Show unit in contrasting color
                    if (stack_item.unit is not None
                            and not stack_item.unit.is_unitless):
                        unit_str = " " + stack_item.unit.display()
                        ucol = x_offset + 2 + len(num_str)
                        remaining = value_width - len(num_str)
                        if remaining > 1:
                            unit_str = truncate(
                                unit_str, remaining
                            ) if len(unit_str) > remaining else unit_str
                            self.window.addstr(
                                row + 1, ucol, unit_str,
                                curses.color_pair(3))

            if truncated and rows_available >= 2:
                last_col_x = (num_cols - 1) * col_width + 1
                self.window.addstr(self.height - 2, last_col_x, "...")
        except curses.error:
            pass

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
                 results_info):
        layout = scr._layout
        if is_menu:
            w = layout.stack.width + layout.history.width
            x = layout.stack.x
            y = layout.stack.y
        else:
            w = layout.history.width + layout.commands.width
            x = layout.history.x
            y = layout.history.y
        h = layout.commands.height

        super().__init__(scr, w, h, x, y)
        self.help_title = help_title
        self.signature_info = signature_info
        self.docstring = docstring
        self.results_info = results_info
        self.refresh()

    def refresh(self):
        self.scr.hide_registers_window()
        try:
            self.window.clear()
            self.window.border()
            max_content_width = self.width - 2
            self.window.addstr(
                1,
                centered_position(self.help_title, self.width),
                self.help_title,
                curses.color_pair(2))

            indent = "    "
            docstring_lines = (indent + i for i in
                               textwrap.wrap(
                                   textwrap.dedent(self.docstring).strip(),
                                   max_content_width - len(indent)))

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
            last_content_row = self.height - 2
            for yposn, text in enumerate(display_iterable, 2):
                if yposn >= last_content_row:
                    self.window.addstr(last_content_row, 1, "...")
                    break
                if max_content_width > 3:
                    text = truncate(text, max_content_width)
                self.window.addstr(yposn, 1, text)
        except curses.error:
            pass
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
        self._layout = None
        self._too_small = False
        self._units_active = False
        self._setup()

    def _setup(self):
        """
        Initialize all the windows making up the esc interface,
        as well as curses settings.
        """
        max_y, max_x = self.stdscr.getmaxyx()

        if max_y < MIN_TERM_HEIGHT or max_x < MIN_TERM_WIDTH:
            self._too_small = True
            self._show_too_small_message(max_y, max_x)
            return

        self._too_small = False
        self._layout = compute_layout(max_y, max_x,
                                      units_active=self._units_active)
        layout = self._layout

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.statusw = StatusWindow(self, layout.status)
        self.stackw = StackWindow(self, layout.stack)
        self.historyw = HistoryWindow(self, layout.history)
        self.commandsw = CommandsWindow(self, layout.commands)
        if layout.registers is not None:
            self.registersw = RegistersWindow(self, layout.registers)
        else:
            self.registersw = _NullWindow()

    def _show_too_small_message(self, max_y, max_x):
        "Display a centered 'terminal too small' message on stdscr."
        self.stdscr.clear()
        msg = (f"Terminal too small ({max_x}x{max_y}). "
               f"Need {MIN_TERM_WIDTH}x{MIN_TERM_HEIGHT}.")
        row = max(0, max_y // 2)
        col = max(0, (max_x - len(msg)) // 2)
        try:
            self.stdscr.addstr(row, col, msg)
        except curses.error:
            pass
        self.stdscr.refresh()

    @property
    def too_small(self):
        return self._too_small

    def handle_resize(self):
        "Recreate all windows after a terminal resize."
        curses.update_lines_cols()
        self.stdscr.clear()
        self.stdscr.refresh()
        self._setup()

    def activate_units(self):
        """One-time transition to wider stack column for unit display."""
        if not self._units_active:
            self._units_active = True
            self.handle_resize()

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
        self.helpw = HelpWindow(self, is_menu, help_title, signature_info,
                                docstring, results_info)


class _NullWindow:
    """Stand-in for a window that isn't displayed (e.g. registers when
    the terminal is too short)."""

    def refresh(self):
        pass

    def clear(self):
        pass

    def update_registry(self, registry):
        pass


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
