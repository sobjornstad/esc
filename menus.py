"""
menus.py - implement menus of functions

We use menus to register and keep track of the functions the user can call.
Actual functions are defined in functions.py (and in a future
user-defined-functions file).

First come EscFunction and its subclasses, which implement both the menus and
the functions in a sort of recursive tree pattern. Then come
faux-constructors (actually functions) which can be imported from
functions.py and called to register functions (we import functions.py from
here so that it gets run). Through these constructors, all registered
functions and submenus end up reachable from the main menu.
"""

from collections import OrderedDict
import copy
import decimal
import itertools

from consts import (QUIT_CHARACTER, UNDO_CHARACTER, REDO_CHARACTER,
                    RETRIEVE_REG_CHARACTER, STORE_REG_CHARACTER, DELETE_REG_CHARACTER)
from display import screen
import modes
from oops import (FunctionExecutionError, InsufficientItemsError, NotInMenuError,
                  ProgrammingError)

BINOP = 'binop'
UNOP = 'unop'


class EscFunction:
    """
    Class for some esc functionality or operation the user can activate.

    When the user activates this item, execute() is called. Execution takes
    any action associated with the item, throwing an exception if something
    didn't work right. It then returns the menu that the interface should
    return to. A return value of None returns to the main menu.
    """
    def __init__(self, key, description):
        self.key = key
        self.description = description
        self.parent = None
        self.children = OrderedDict()

    # pylint: disable=unused-argument, no-self-use
    # not sure why pylint is so unable to recognize this is an abstract method
    def execute(self, access_key, ss):
        return NotImplementedError

    def register_child(self, child):
        """
        Register a new child of this menu (whether a menu or an operation).
        """
        child.parent = self
        self.children[child.key] = child


class EscMenu(EscFunction):
    """
    A type of EscFunction that serves as a container for other menus and operations.
    """
    def __init__(self, key, description, mode_display=None):
        super().__init__(key, description)
        self.mode_display = mode_display

    def __repr__(self):
        return (f"<EscMenu '{self.key}': [" +
                ", ".join(repr(i) for i in self.children.values()) +
                "]>")

    @property
    def is_main_menu(self):
        """
        This is the main menu if it has no parent.

        Obviously a menu that's wrongly never been connected to anything
        could cause a false positive, but then we normally would not be able
        to obtain a reference to it anyway.
        """
        return self.parent is None

    @property
    def anonymous_children(self):
        """
        Iterate over children without a description. These are listed
        differently in menus and so on.
        """
        for i in self.children.values():
            if not i.description:
                yield i

    @property
    def named_children(self):
        "Iterate over children with a description."
        for i in self.children.values():
            if i.description:
                yield i

    def execute(self, access_key, ss):
        if access_key == QUIT_CHARACTER:
            if self.is_main_menu:
                raise SystemExit(1)
            else:
                return self.parent

        try:
            child = self.children[access_key]
        except KeyError:
            raise NotInMenuError(
                f"There's no option '{access_key}' in this menu.")

        if isinstance(child, EscMenu):
            return child
        else:
            return child.execute(access_key, ss)


class EscOperation(EscFunction):
    """
    A type of EscFunction that can be run to make some changes on the stack.
    """
    def __init__(self, key, func, pop, push, description, menu, log_as=None):
        super().__init__(key, description)
        self.function = func
        self.pop = pop
        self.push = push
        self.parent = menu
        self.log_as = log_as

    def __repr__(self):
        return f"<EscOperation '{self.key}': {self.description}"

    def _insufficient_items_on_stack(self, pops_requested=None):
        "Call for a FunctionExecutionError() if the stack is too empty."
        if pops_requested is None:
            pops_requested = self.pop
            assert pops_requested != -1  # caller needs to reset the value if it is
        pops = 'item' if pops_requested == 1 else 'items'
        msg = f"'{self.key}' needs at least {pops_requested} {pops} on stack."
        return FunctionExecutionError(msg)

    def describe_operation(self, args, retvals):
        """
        Given the values popped from the stack (args) and the values pushed
        back to the stack (retvals), return a string describing what was done.
        """
        if self.log_as is None:
            return self.description
        elif self.log_as == UNOP:
            return f"{self.description} {args[0]} = {retvals[0]}"
        elif self.log_as == BINOP:
            return f"{args[0]} {self.key} {args[1]} = {retvals[0]}"
        elif callable(self.log_as):
            return self.log_as(args, retvals)
        else:
            return self.log_as.format(*itertools.chain(args, retvals))

    def execute(self, access_key, ss):  # pylint: disable=useless-return
        with ss.transaction():
            args = self.retrieve_arguments(ss)
            try:
                retvals = self.function(args)
            except ValueError:
                # illegal operation; restore original args to stack and return
                raise FunctionExecutionError("Domain error! Stack unchanged.")
            except ZeroDivisionError:
                raise FunctionExecutionError(
                    "Sorry, division by zero is against the law.")
            except decimal.InvalidOperation:
                raise FunctionExecutionError(
                    "That operation is not defined by the rules of arithmetic.")
            except InsufficientItemsError as e:
                raise self._insufficient_items_on_stack(e.number_required)
            self.store_results(ss, args, retvals)
        return None

    def retrieve_arguments(self, ss):
        """
        Get a slice of stack from /ss/ of the size requested by the function
        we're calling, throwing an exception if this can't be completed.
        """
        # Enter the number currently being edited, if any, stopping if it is
        # invalid.
        try:
            ss.enter_number(running_op=self.key)
        except ValueError as e:
            raise FunctionExecutionError(str(e))

        # Make sure there will be space to push the results.
        # If requesting the whole stack, it's the function's responsibility to check.
        if not ss.has_push_space(self.push - self.pop) and self.pop != -1:
            num_short = self.push - self.pop - ss.free_stack_spaces
            spaces = 'space' if num_short == 1 else 'spaces'
            msg = f"'{self.key}': stack is too full (short {num_short} {spaces})."
            raise FunctionExecutionError(msg)

        if self.pop == -1:
            # Whole stack requested; will push the whole stack back later.
            args = copy.deepcopy(ss.s)
            ss.clear()
        else:
            args = ss.pop(self.pop)
            if (not args) and self.pop != 0:
                raise self._insufficient_items_on_stack()

        return args

    def store_results(self, ss, args, return_values):
        """
        Return the values computed by our function to the stack.
        """
        if self.push > 0 or (self.push == -1 and return_values is not None):
            if not hasattr(return_values, '__iter__'):
                return_values = (return_values,)

            coerced_retvals = []
            for i in return_values:
                # Functions can return any type that can be converted to Decimal.
                if not isinstance(i, decimal.Decimal):
                    try:
                        coerced_retvals.append(decimal.Decimal(i))
                    except decimal.InvalidOperation as e:
                        raise ProgrammingError(
                            "An esc function returned a value that cannot be "
                            "converted to a Decimal. The original error message is as "
                            "follows:\n%r" % e)
                else:
                    coerced_retvals.append(i)

            ss.push(coerced_retvals, self.describe_operation(args, return_values))
        else:
            ss.record_operation(self.describe_operation(args, ()))


### Constructor/registration functions to be used in functions.py ###
def Menu(key, description, parent, mode_display=None):  # pylint: disable=invalid-name
    "Create a new menu under the existing menu /parent/."
    menu = EscMenu(key, description, mode_display)
    parent.register_child(menu)
    return menu


main_menu = EscMenu('', "Main Menu")  # pylint: disable=invalid-name


def Constant(value, key, description, menu):  # pylint: disable=invalid-name
    "Create a new constant. Syntactic sugar for registering a function."
    op = EscOperation(key=key, func=lambda _: value, pop=0, push=1,
                      description=description, menu=menu,
                      log_as=f"insert constant '{description}'")
    menu.register_child(op)


def Function(key, menu, push, pop, description=None, log_as=None):  # pylint: disable=invalid-name
    """
    Decorator to register a function on a given menu.
    """
    def function_decorator(func):
        op = EscOperation(key=key, func=func, pop=pop, push=push,
                          description=description, menu=menu, log_as=log_as)
        menu.register_child(op)
        return func
    return function_decorator


def Mode(name, default_value, allowable_values=None):  # pylint: disable=invalid-name
    return modes.register(name, default_value, allowable_values)


def ModeChange(key, description, menu, mode_name, to_value):  # pylint: disable=invalid-name
    "Create a new mode change. Syntactic sugar for registering a function."
    op = EscOperation(key=key, func=lambda _: modes.set(mode_name, to_value),
                      pop=0, push=0, description=description, menu=menu)
    menu.register_child(op)


import functions


def display_menu(menu):
    """
    Update the commands window to show the current menu.
    """
    screen().reset_commands_window()

    min_xposn = 2
    max_xposn = 22
    xposn = 2
    yposn = 1

    # Print menu title.
    if not menu.is_main_menu:
        screen().add_menu(menu.description, yposn)
        if menu.mode_display:
            screen().add_mode_display(menu.mode_display(), yposn+1)
        yposn += 2

    # Print anonymous functions to the screen.
    for i in menu.anonymous_children:
        screen().add_command(i.key, None, yposn, xposn)
        xposn += 2
        if xposn >= max_xposn - 2:
            yposn += 1
            xposn = min_xposn

    # Now normal functions and menus.
    yposn += 1
    xposn = min_xposn
    for i in menu.named_children:
        screen().add_command(i.key, i.description, yposn, xposn)
        yposn += 1

    # then the special options, if on the main menu
    if menu.is_main_menu:
        screen().add_command(STORE_REG_CHARACTER, 'store bos to reg', yposn, xposn)
        screen().add_command(RETRIEVE_REG_CHARACTER, 'get bos from reg', yposn+1, xposn)
        screen().add_command(DELETE_REG_CHARACTER, 'delete register', yposn+2, xposn)
        screen().add_command(UNDO_CHARACTER, 'undo (', yposn+3, xposn)
        screen().add_command(REDO_CHARACTER.lower(), 'redo)', yposn+3, xposn + 8)
        yposn += 4

    # then the quit option, which is always there but is not a function
    quit_name = 'quit' if menu.is_main_menu else 'cancel'
    screen().add_command(QUIT_CHARACTER, quit_name, yposn, xposn)

    # finally, make curses figure out how it's supposed to draw this
    screen().commandsw.refresh()
