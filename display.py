"""
display.py - drive the curses interface

Other modules call into the EscScreen singleton defined here when they need
to update the screen.
"""

import curses
from consts import STACKDEPTH, STACKWIDTH, PROGRAM_NAME

# pylint: disable=invalid-name
_screen = None


class Window:
    "One of the curses windows making up esc's interface."
    width = None
    height = None
    start_x = None
    start_y = None

    def __init__(self, scr):
        self.scr = scr
        self.window = curses.newwin(self.height, self.width, self.start_y, self.start_x)

    def refresh(self):
        if self.window is not None:
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

    def __init__(self, scr, max_x):
        self.width = max_x
        super().__init__(scr)

        self.status_char = ' '
        self.status_msg = ''

        self.window.addstr(0, 0, (' ' * 79), curses.color_pair(1))
        self.window.addstr(0, 0, f"[{self.status_char}] {PROGRAM_NAME} |",
                           curses.color_pair(1))
        self.window.move(0, 1)
        self.refresh()

    def refresh(self):
        self.window.addstr(0, 1, self.status_char, curses.color_pair(1))
        self.window.addstr(0, 16, ' ' * (79 - 15), curses.color_pair(1))
        self.window.addstr(0, 16, self.status_msg, curses.color_pair(1))
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

    def __init__(self, scr):
        super().__init__(scr)
        self.ss = None

        self.window.border()
        self.window.addstr(0, 9, "Stack")
        self.refresh()

    def refresh(self):
        self.window.clear()
        self.window.border()
        self.window.addstr(0, 9, "Stack")
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

    def __init__(self, scr):
        super().__init__(scr)
        self.window.border()
        self.window.addstr(0, 13, "History")
        self.refresh()


class CommandsWindow(Window):
    "Window displaying available commands/actions."
    width = 24
    start_x = 56
    start_y = 1

    def __init__(self, scr, max_y):
        self.height = max_y - 1
        super().__init__(scr)
        self.commands = []
        self.refresh()

    def refresh(self):
        self.window.clear()
        self.window.border()
        self.window.addstr(0, 8, "Commands")

        # TODO: This is desperately ugly and is intended to be a hack until
        # commands are objects we can introspect.
        for command in self.commands:
            try:
                self.window.addstr(*command[:-1])
                if command[-1]:
                    self.window.addstr(command[0],
                                       command[1] + 1 + len(command[2]),
                                       command[-1])
            except curses.error:
                pass
        super().refresh()

    def add_menu(self, text, yposn):
        text = "(%s)" % text
        ctrxpos = (STACKWIDTH - len(text)) // 2 + 1
        self.add_command('', text, yposn, ctrxpos)

    def add_mode_display(self, text, yposn):
        ctrxpos = (STACKWIDTH - len(text)) // 2 + 1
        self.add_command('', text, yposn, ctrxpos)

    def add_command(self, char, descr, yposn, xposn):
        self.commands.append((yposn, xposn, char, curses.color_pair(2), descr))

    def reset(self):
        self.commands.clear()


class RegistersWindow(Window):
    "Window displaying registers/variables currently defined."
    width = 56
    start_x = 0
    start_y = 4 + STACKDEPTH

    def __init__(self, scr, max_y):
        self.height = max_y - 1 - (3 + STACKDEPTH)
        super().__init__(scr)
        self.window.border()
        self.window.addstr(0, 24, "Registers")
        self.refresh()

    def update_registers(self, registry):
        """
        Update the registers window to show the current registry values.
        """
        for yposn, (register, stack_item) in enumerate(registry.items(), 1):
            assert len(register) == 1
            self.window.addstr(yposn, 1, register, curses.color_pair(2))
            self.window.addstr(yposn, 3, str(stack_item))

        self.refresh()


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
        self._setup()

    def _setup(self):
        """
        Initialize all the windows making up the esc interface,
        as well as curses settings.
        """
        max_y, max_x = self.stdscr.getmaxyx()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

        self.statusw = StatusWindow(self, max_x)
        self.stackw = StackWindow(self)
        self.historyw = HistoryWindow(self)
        self.commandsw = CommandsWindow(self, max_y)
        self.registersw = RegistersWindow(self, max_y)


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
        self.registersw.update_registers(registry)

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
