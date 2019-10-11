"""
menus.py - implement menus of functions

We use menus to register and keep track of the functions the user can call.
Actual functions are defined in functions.py (and in a future
user-defined-functions file).

First come EscFunction and its subclasses, which implement both the menus and
the functions in a composite tree pattern. Then come faux-constructors
(actually functions) which can be imported from functions.py and called to
register functions (we import functions.py from here so that it gets run).
Through these constructors, all registered functions and submenus end up
reachable from the main menu.
"""

from collections import OrderedDict
import decimal
from functools import wraps
from inspect import signature, Parameter
import itertools

from consts import (QUIT_CHARACTER, UNDO_CHARACTER, REDO_CHARACTER,
                    RETRIEVE_REG_CHARACTER, STORE_REG_CHARACTER, DELETE_REG_CHARACTER)
from display import screen
import modes
from oops import (FunctionExecutionError, InsufficientItemsError, NotInMenuError,
                  FunctionProgrammingError, ProgrammingError)
import util

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
    is_menu = False

    def __init__(self, key, description):
        self.key = key
        self.description = description
        self.parent = None
        self.children = OrderedDict()

    @property
    def help_title(self):
        raise NotImplementedError

    @property
    def signature_info(self):
        raise NotImplementedError

    def simulated_result(self, ss, registry):  # pylint: disable=no-self-use, unused-argument
        return None

    def execute(self, access_key, ss, registry):
        raise NotImplementedError

    def register_child(self, child):
        """
        Register a new child of this menu (whether a menu or an operation).
        """
        if child.key in self.children:
            conflicting = self.children[child.key].description
            raise ProgrammingError(
                f"Cannot add '{child.description}' as a child of '{self.description}':"
                f" the access key '{child.key}' is already in use for '{conflicting}'.")

        child.parent = self
        self.children[child.key] = child


class EscMenu(EscFunction):
    """
    A type of EscFunction that serves as a container for other menus and operations.
    """
    is_menu = True

    def __init__(self, key, description, doc, mode_display=None):
        super().__init__(key, description)
        self.__doc__ = doc
        self.mode_display = mode_display

    def __repr__(self):
        return (f"<EscMenu '{self.key}': [" +
                ", ".join(repr(i) for i in self.children.values()) +
                "]>")

    @property
    def help_title(self):
        if self.description:
            return f"{self.key} ({self.description})"
        else:
            return self.key

    @property
    def signature_info(self):
        return ("    Type: Menu (categorizes operations)",)

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

    def child(self, access_key):
        """
        Return the child defined by /access_key/. Raises NotInMenuError
        if it doesn't exist.
        """
        try:
            return self.children[access_key]
        except KeyError:
            raise NotInMenuError(access_key)

    def execute(self, access_key, ss, registry):
        if access_key == QUIT_CHARACTER:
            if self.is_main_menu:
                raise SystemExit(1)
            else:
                return self.parent

        child = self.child(access_key)
        if isinstance(child, EscMenu):
            return child
        else:
            return child.execute(access_key, ss, registry)


class EscOperation(EscFunction):
    """
    A type of EscFunction that can be run to make some changes on the stack.
    """
    def __init__(self, key, func, pop, push, description, menu, retain=False,
                 log_as=None):  # pylint: disable=too-many-arguments
        super().__init__(key, description)
        self.function = func
        self.pop = pop
        self.push = push
        self.parent = menu
        self.retain = retain
        self.log_as = log_as

    def __repr__(self):
        return f"<EscOperation '{self.key}': {self.description}"

    @property
    def __doc__(self):
        if self.function.__doc__ is None:
            return "The author of this function has not provided a description."
        else:
            return self.function.__doc__

    @property
    def help_title(self):
        if self.description:
            return f"{self.key} ({self.description})"
        else:
            return self.key

    @property
    def signature_info(self):
        items = "item" if self.pop == 1 else "items"
        results = "result" if self.push == 1 else "results"
        type_ = f"    Type: Function (performs calculations)"

        if self.pop == -1:
            input_ = f"    Input: entire stack"
        else:
            input_ = f"    Input: {self.pop} {items} from the stack"

        if self.retain:
            input_ += " (will remain)"

        if self.push == -1:
            output = "    Output: any number of items"
        elif self.push == 0:
            output = "    Output: no output"
        else:
            output = f"    Output: {self.push} {results} added to the stack"

        return (type_, input_, output)

    def _simulated_description(self, args, log, results):
        """
        Return a list of strings to display in esc's interface to describe an
        operation that takes /args/, produces a log message of /log/, and
        outputs /results/.
        """
        description = [f"This calculation would occur:",
                       f"    {log}"]
        if self.retain:
            description.append("The following stack items would be read as input:")
        else:
            description.append("The following stack items would be consumed:")

        if args:
            for i in args:
                description.append(f"    {i}")
        else:
            description.append("    (none)")

        description.append("The following results would be returned:")
        if results:
            for i in results:
                description.append(f"    {i}")
        else:
            description.append("    (none)")
        return description

    def _insufficient_items_on_stack(self, pops_requested=None):
        "Call for a FunctionExecutionError() if the stack is too empty."
        if pops_requested is None:
            pops_requested = self.pop
            assert pops_requested != -1  # caller needs to reset the value if it is
        pops = 'item' if pops_requested == 1 else 'items'
        msg = f"'{self.key}' needs at least {pops_requested} {pops} on stack."
        return InsufficientItemsError(pops_requested, msg)

    def _retrieve_arguments(self, ss):
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
            args = ss.s[:]
            if not self.retain:
                ss.clear()
        else:
            args = ss.pop(self.pop, retain=self.retain)
            if (not args) and self.pop != 0:
                raise self._insufficient_items_on_stack()

        return args

    def _store_results(self, ss, args, return_values, registry):
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
                    except (decimal.InvalidOperation, TypeError) as e:
                        raise FunctionProgrammingError(
                            function_name=self.function.__name__,
                            key=self.key,
                            description=self.description,
                            problem="returned a value that cannot be converted "
                                    "to a Decimal",
                            wrapped_exception=e)
                else:
                    coerced_retvals.append(i)

            ss.push(coerced_retvals,
                    self.describe_operation(args, return_values, registry))
        else:
            ss.record_operation(self.describe_operation(args, (), registry))

    def describe_operation(self, args, retvals, registry):
        """
        Given the values popped from the stack (args) and the values pushed
        back to the stack (retvals), return a string describing what was done.
        """
        if self.log_as is None:
            return self.description
        elif self.log_as == UNOP:
            try:
                return f"{self.description} {args[0]} = {retvals[0]}"
            except IndexError:
                raise FunctionProgrammingError(
                    function_name=self.function.__name__,
                    key=self.key,
                    description=self.description,
                    problem="requested unary operator logging (UNOP) but did not "
                            "request any values from the stack")
        elif self.log_as == BINOP:
            try:
                return f"{args[0]} {self.key} {args[1]} = {retvals[0]}"
            except IndexError:
                raise FunctionProgrammingError(
                    function_name=self.function.__name__,
                    key=self.key,
                    description=self.description,
                    problem="requested binary operator logging (BINOP) but did not "
                            "request two values from the stack")
        elif callable(self.log_as):
            return util.magic_call(
                self.log_as,
                {'args': args, 'retval': retvals, 'registry': registry})
        else:
            return self.log_as.format(*itertools.chain(args, retvals))

    def execute(self, access_key, ss, registry):  # pylint: disable=useless-return
        with ss.transaction():
            args = self._retrieve_arguments(ss)
            try:
                retvals = self.function(args, registry)
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
            self._store_results(ss, args, retvals, registry)
        return None  # back to main menu

    def simulated_result(self, ss, registry):
        """
        Execute the operation on the provided StackState, but don't actually
        change the state -- instead, provide a description of what would
        happen.
        """
        used_args = ss.last_n_items(self.pop)
        checkpoint = ss.memento()
        try:
            self.execute(None, ss, registry)
            results = ss.last_n_items(self.push)
            log_message = ss.last_operation
        except InsufficientItemsError as e:
            items = "item is" if e.number_required == 1 else "items are"
            return (
                f"An error would occur. (At least {e.number_required} stack {items}",
                f"needed to run this function.)")
        except FunctionExecutionError:
            return ("An error would occur. (Most likely the values on ",
                    "the stack are not valid.)")
        finally:
            ss.restore(checkpoint)

        return self._simulated_description(used_args, log_message, results)


class BuiltinFunction(EscFunction):
    """
    Mock class for built-in functions. Built-in EscFunctions do not actually
    get run and do anything -- they are special-cased because they need
    access to internals normal functions cannot access. However, it's still
    useful to have classes for them as stand-ins for things like retrieving
    help.

    Unlike the other EscFunctions, we subclass these because they each need
    special behaviors. Subclasses should override the docstring (directly is
    fine) and the simulated_result() method.

    Subclasses should define key and description as class variables. They'll
    be shadowed by instance variables once we instantiate the class, but the
    values will be the same. That sounds dumb, but it makes sense for all
    other classes in the hierarchy and doesn't hurt us here. We don't want to
    define them in the __init__ of each subclass because then we have to
    instantiate every class to match on them by key (see reflective search in
    helpme.py).
    """
    def __init__(self):
        super().__init__(self.key, self.description)
        self.is_menu = False

    def execute(self, access_key, ss, registry):  # pylint: disable=useless-return
        pass

    @property
    def help_title(self):
        return f"{self.key} ({self.description})"

    @property
    def signature_info(self):
        type_ = f"    Type: Built-in (performs special esc actions)"
        return (type_,)


### Constructor/registration functions to be used in functions.py ###
def Menu(key, description, parent, doc, mode_display=None):  # pylint: disable=invalid-name
    "Create a new menu under the existing menu /parent/."
    menu = EscMenu(key, description, doc, mode_display)
    parent.register_child(menu)
    return menu


# As I write this, if the user ever sees this docstring, something's probably
# gone wrong, since there's no way to choose the main menu from a menu and thus
# get its help, but in the interest of future-proofing, we'll say something
# interesting.
main_doc = """
    The main menu. All other esc functions and menus are eventually accessible
    from this menu.
"""
main_menu = EscMenu('', "Main Menu", doc=main_doc)  # pylint: disable=invalid-name


def Constant(value, key, description, menu):  # pylint: disable=invalid-name
    "Create a new constant. Syntactic sugar for registering a function."
    @Function(key=key, menu=menu, push=1, description=description,
              log_as=f"insert constant {description}")
    def func():
        return value
    # You can't define a dynamic docstring from within the function.
    func.__doc__ = f"Add the constant {description} = {value} to the stack."


def Function(key, menu, push, description=None, retain=False, log_as=None):  # pylint: disable=invalid-name
    """
    Decorator to register a function on a given menu.
    """
    def function_decorator(func):
        sig = signature(func)
        parms = sig.parameters.values()

        bind_all = [i for i in parms if i.kind == Parameter.VAR_POSITIONAL]
        stack_parms = [i for i in parms if i.name not in ('registry',)]
        pop = len(stack_parms) if not bind_all else -1

        def _bind_stack_parm(stack_item, parm):
            if parm.name.endswith('_stackitem'):
                return stack_item
            if parm.name.endswith('_str'):
                return stack_item.string
            else:
                return stack_item.decimal

        @wraps(func)
        def wrapper(stack, registry):
            positional_binding = []
            keyword_binding = {}

            if bind_all:
                positional_binding.extend(_bind_stack_parm(stack_item, bind_all[0])
                                          for stack_item in stack)
            else:
                stack_slice = stack[-(len(stack_parms)):]
                keyword_binding.update({parm.name: _bind_stack_parm(stack_item, parm)
                                        for stack_item, parm
                                        in zip(stack_slice, stack_parms)})
            if 'registry' in (i.name for i in parms):
                keyword_binding['registry'] = registry
            return func(*positional_binding, **keyword_binding)

        op = EscOperation(key=key, func=wrapper, pop=pop, push=push,
                          description=description, menu=menu, log_as=log_as,
                          retain=retain)
        menu.register_child(op)
        return wrapper

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

    min_xposn = 1
    max_xposn = 22
    xposn = min_xposn
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
