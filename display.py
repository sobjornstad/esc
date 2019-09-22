import curses
from consts import STACKDEPTH, STACKWIDTH, PROGRAM_NAME

_screen = None


class Window:
    def __init__(self, scr):
        self.scr = scr
        self.window = None

    def refresh(self):
        if self.window is not None:
            self.window.refresh()

    def getch(self):
        return self.window.getch()

    def putch(self, c):
        self.window.addstr(c)


class StatusWindow(Window):
    def __init__(self, scr, max_x):
        super().__init__(scr)

        self.status_char = ' '
        self.status_msg = ''

        self.window = curses.newwin(1, max_x, 0, 0)
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
    def __init__(self, scr):
        super().__init__(scr)
        self.ss = None

        self.window = curses.newwin(3 + STACKDEPTH, 24, 1, 0)
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
        if self.ss.editing_last_item:
            self.window.move(1 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        else:
            # when not editing a number, cursor goes on *next line*
            self.window.move(2 + self.ss.stack_posn, self.ss.cursor_posn + 1)

    def backspace(self, status):
        if status == 0:  # character backspaced
            self.window.addstr(1 + self.ss.stack_posn, self.ss.cursor_posn + 1, ' ')
            self.window.move(1 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        elif status == 1:  # stack item wiped out
            self.window.addstr(2 + self.ss.stack_posn, self.ss.cursor_posn + 1, ' ')
            self.window.move(2 + self.ss.stack_posn, self.ss.cursor_posn + 1)
        else:  # nothing to backspace
            pass


class HistoryWindow(Window):
    def __init__(self, scr):
        super().__init__(scr)
        self.window = curses.newwin(3 + STACKDEPTH, 32, 1, 24)
        self.window.border()
        self.window.addstr(0, 13, "History")
        self.refresh()


class CommandsWindow(Window):
    def __init__(self, scr):
        super().__init__(scr)
        self.window = curses.newwin(3 + STACKDEPTH, 24, 1, 56)
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

    def add_menu(self, text, yposn, xposn):
        text = "(%s)" % text
        ctrxpos = (STACKWIDTH - len(text)) // 2 + 1
        self.add_command('', text, yposn, ctrxpos)

    def add_mode_display(self, text, yposn, xposn):
        ctrxpos = (STACKWIDTH - len(text)) // 2 + 1
        self.add_command('', text, yposn, ctrxpos)

    def add_command(self, char, descr, yposn, xposn):
        self.commands.append((yposn, xposn, char, curses.color_pair(2), descr))

    def reset(self):
        self.commands.clear()


class RegistersWindow(Window):
    def __init__(self, scr, max_y):
        super().__init__(scr)
        self.window = curses.newwin(max_y - 1 - (3 + STACKDEPTH), 80, 4 + STACKDEPTH, 0)
        self.window.border()
        self.window.addstr(0, 36, "Registers")
        self.refresh()


class EscScreen:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.statusw = None
        self.stackw = None
        self.historyw = None
        self.commandsw = None
        self.registersw = None
        self._setup()

    def _setup(self):
        max_y, max_x = self.stdscr.getmaxyx()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

        self.statusw = StatusWindow(self, max_x)
        self.stackw = StackWindow(self)
        self.historyw = HistoryWindow(self)
        self.commandsw = CommandsWindow(self)
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
    def add_menu(self, text, yposn, xposn):
        self.commandsw.add_menu(text, yposn, xposn)

    def add_mode_display(self, text, yposn, xposn):
        self.commandsw.add_mode_display(text, yposn, xposn)

    def add_command(self, char, descr, yposn, xposn):
        self.commandsw.add_command(char, descr, yposn, xposn)

    def reset_commands_window(self):
        self.commandsw.reset()

def screen():
    return _screen


def init(stdscr):
    global _screen
    _screen = EscScreen(stdscr)
