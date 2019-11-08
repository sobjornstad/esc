"""
commands.py - implement menus, operations, and other things that show up
              in the commands window

We use menus to register and keep track of the commands the user can choose.
Actual calculator functionality is defined in functions.py (and in user
plugins).

First come EscCommand and its subclasses, which implement both menus and
operations (which wrap the actual Python functions in functions.py that
perform calculations) in a composite tree pattern. Then come
faux-constructors (actually functions) which can be imported from
functions.py and called to register functions as operations. Through these
constructors, all registered operations and submenus end up reachable from
the main menu.
"""

from collections import OrderedDict
import decimal
from functools import wraps
from inspect import signature, Parameter
import itertools

from . import consts
from .functest import TestCase
from . import modes
from .oops import (FunctionExecutionError, InsufficientItemsError, NotInMenuError,
                   FunctionProgrammingError, ProgrammingError)
from . import util

BINOP = 'binop'
UNOP = 'unop'


class EscCommand:
    """
    Base class for some esc functionality or operation the user can activate.

    When the user activates this item, :meth:`execute` is called. Execution
    takes any action associated with the item, throwing an exception if
    something didn't work right. It then returns the menu that the interface
    should return to. A return value of None returns to the main menu.
    """
    #: Class variable describing whether this class is a menu or not.
    #  External code may occasionally need to know the difference.
    is_menu = False

    def __init__(self, key, description):
        #: The key used to activate this item on its parent menu.
        self.key = key
        #: How this item is described on its parent menu.
        self.description = description
        #: An :class:`EscCommand` (hopefully a menu) this item is contained in.
        self.parent = None
        #: Mapping from keys to :class:`EscCommand`\ s on the current menu,
        #: if this is a menu. Add to this using :meth:`register_child()`, not directly.
        self.children = OrderedDict()

    @property
    def help_title(self):
        """
        The title this command should show in the help system. This is the
        access key and description if a description is defined; otherwise it
        is just the access key.
        """
        if self.description:
            return f"{self.key} ({self.description})"
        else:
            return self.key


    @property
    def signature_info(self):
        """An iterable of strings to display under the "Signature" section in help."""
        raise NotImplementedError

    def execute(self, access_key, ss, registry):
        """
        Execute this EscCommand. For operations or builtins, this involves
        the class doing its own work; for menus, this returns the child
        defined by *access_key*.

        :return: An instance of :class:`EscCommand` representing the menu
                 the UI should now return to,
                 or ``None`` to indicate the main menu.
        """
        raise NotImplementedError

    def register_child(self, child):
        """
        Register a new child :class:`EscCommand` of this menu (either a menu
        or an operation). This operation doesn't make sense for
        :class:`EscOperation` instances; the caller should avoid doing this.
        """
        if child.key in self.children:
            conflicting = self.children[child.key].description
            raise ProgrammingError(
                f"Cannot add '{child.description}' as a child of '{self.description}':"
                f" the access key '{child.key}' is already in use for '{conflicting}'.")

        child.parent = self
        self.children[child.key] = child

    def simulated_result(self, ss, registry):  # pylint: disable=no-self-use, unused-argument
        """
        Execute this command against the given stack state and registry, but
        instead of actually changing the state, return a string describing
        the result.

        May return ``None`` if the :class:`EscCommand` does not change the
        stack state (e.g., a menu).
        """
        return None

    def test(self):
        """
        Execute any self-tests associated with this :class:`EscCommand`.
        If a test fails, raise a
        :class:`ProgrammingError <esc.oops.ProgrammingError>`.
        """
        raise NotImplementedError


class EscMenu(EscCommand):
    """
    A type of EscCommand that serves as a container for other menus
    and operations. Executing it activates a child item.
    """
    is_menu = True

    def __init__(self, key, description, doc, mode_display=None):
        super().__init__(key, description)
        self.__doc__ = doc
        #: An optional callable whose return value will be shown under the menu title.
        self.mode_display = mode_display

    def __repr__(self):
        return (f"<EscMenu '{self.key}': [" +
                ", ".join(repr(i) for i in self.children.values()) +
                "]>")

    @property
    def signature_info(self):
        "Constant string that describes the menu as a menu."
        return ("    Type: Menu (categorizes operations)",)

    @property
    def is_main_menu(self):
        "This is the main menu if it has no parent."
        return self.parent is None

    @property
    def anonymous_children(self):
        "Iterable of children without a description."
        for i in self.children.values():
            if not i.description:
                yield i

    @property
    def named_children(self):
        "Iterable of children with a description."
        for i in self.children.values():
            if i.description:
                yield i

    def child(self, access_key):
        """
        Return the child defined by *access_key*.
        Raises :class:`NotInMenuError <esc.oops.NotInMenuError>`
        if it doesn't exist.
        """
        try:
            return self.children[access_key]
        except KeyError:
            raise NotInMenuError(access_key)

    def execute(self, access_key, ss, registry):
        """
        Look up the child described by *access_key* and execute it. If said
        child is a menu, return it (so the user can choose an item from that
        menu). Otherwise, execute the child immediately.

        :param access_key: A menu access key indicating which child to execute.
        :param ss: The current stack state, passed through to a child operation.
        :param registry: The current registry, passed through to a child operation.

        :return: The :class:`EscMenu` to display next,
                 or ``None`` to return to the main menu.
                 This will be a child menu, if one was selected,
                 or None if an operation runs.

        :raises: :class:`FunctionExecutionError <esc.oops.FunctionExecutionError>`
                 or a subclass, if a child operation was selected
                 but does not complete successfully.

        If the user chose the special quit command, return to the previous
        menu, or raise ``SystemExit`` if this is the main menu.
        """
        if access_key == consts.QUIT_CHARACTER:
            if self.is_main_menu:
                raise SystemExit(0)
            else:
                return self.parent

        child = self.child(access_key)
        if child.is_menu:
            return child
        else:
            return child.execute(access_key, ss, registry)

    def test(self):
        "Execute the test method of all children."
        old_testing = consts.TESTING
        consts.TESTING = True
        try:
            for child in self.children.values():
                child.test()
        finally:
            consts.TESTING = old_testing


class EscOperation(EscCommand):
    """
    A type of EscCommand that can be run to make some changes on the stack.
    """
    # pylint: disable=too-many-arguments
    def __init__(self, key, func, pop, push, description, menu, retain=False,
                 log_as=None, simulate=True):
        super().__init__(key, description)
        self.parent = menu
        #: The function, decorated with :func:`@Operation <Operation>`,
        #: that defines the logic of this operation.
        self.function = func
        #: The number of items the function gets from the bottom of the stack.
        #: ``-1`` indicates the entire stack is popped.
        self.pop = pop
        #: The number of items the function returns to the stack.
        #: ``-1`` indicates a variable number of items will be returned.
        self.push = push
        #: If true, items pulled from the stack before execution won't be removed.
        self.retain = retain
        #: A description of how to log this function's execution
        #: (see the docs for :func:`@Operation <Operation>`
        #: for details on allowable values).
        self.log_as = log_as
        #: Whether this function should be run when a simulation is requested for
        #: help purposes. Turn off if the function is slow or has side effects.
        self.simulate_allowed = simulate

    def __repr__(self):
        return f"<EscOperation '{self.key}': {self.description}"

    @property
    def __doc__(self):
        if self.function.__doc__ is None:
            return "The author of this operation has not provided a description."
        else:
            return self.function.__doc__

    @property
    def signature_info(self):
        """
        A description of the function's signature as a tuple of strings
        (one per line to display in the help system),
        based on the :attr:`pop` and :attr:`push` values.
        """
        items = "item" if self.pop == 1 else "items"
        results = "result" if self.push == 1 else "results"
        type_ = f"    Type: Operation (performs calculations)"

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

    def _describe_operation(self, args, retvals, registry):
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
                    operation=self,
                    problem="requested unary operator logging (UNOP) but did not "
                            "request any values from the stack")
        elif self.log_as == BINOP:
            try:
                return f"{args[0]} {self.key} {args[1]} = {retvals[0]}"
            except IndexError:
                raise FunctionProgrammingError(
                    operation=self,
                    problem="requested binary operator logging (BINOP) but did not "
                            "request two values from the stack")
        elif callable(self.log_as):
            return util.magic_call(
                self.log_as,
                {'args': args, 'retval': retvals, 'registry': registry})
        else:
            return self.log_as.format(*itertools.chain(args, retvals))

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

    def _store_results(self, ss, args, return_values, registry):
        """
        Return the values computed by our function to the stack
        and record the operation in a history entry.
        """
        if self.push > 0 or (self.push == -1 and return_values is not None):
            if not hasattr(return_values, '__iter__'):
                return_values = (return_values,)

            try:
                coerced_retvals = util.decimalize_iterable(return_values)
            except (decimal.InvalidOperation, TypeError) as e:
                raise FunctionProgrammingError(
                    operation=self,
                    problem="returned a value that cannot be converted "
                            "to a Decimal") from e
            ss.push(coerced_retvals,
                    self._describe_operation(args, return_values, registry))
        else:
            ss.record_operation(self._describe_operation(args, (), registry))

    def execute(self, access_key, ss, registry):  # pylint: disable=useless-return
        """
        Execute the esc operation wrapped by this instance on the given stack
        state and registry.

        :param access_key: Not used by this subclass.
        :param ss: The current stack state, passed through to a child operation.
        :param registry: The current registry, passed through to a child operation.

        :return: A constant ``None``,
                 indicating that we go back to the main menu.

        :raises: :class:`FunctionExecutionError <esc.oops.FunctionExecutionError>`
                 or a subclass,
                 if the operation cannot be completed successfully.
        """
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
        Execute the operation on the provided `StackState`,
        but don't actually change the state --
        instead, provide a description of what would happen.
        """
        if not self.simulate_allowed:
            return ("The author of this operation has disabled", "simulations.")

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

    def test(self):
        r"""
        If the function on this :class:`EscOperation` has associated
        :class:`TestCase <esc.functest.TestCase>`\ s
        defined in its *tests* attribute,
        execute those tests.
        """
        # Some internal functions that are registered, such as mode changes,
        # don't have a tests attribute. We want to ignore those.
        if hasattr(self.function, 'tests'):
            for test_case in self.function.tests:
                test_case.execute(self)


class EscBuiltin(EscCommand):
    r"""
    Mock class for built-in commands. Built-in :class:`EscCommand`\ s do not
    actually get run and do anything -- they are special-cased because they
    need access to internals normal commands cannot access. However, it's
    still useful to have classes for them as stand-ins for things like
    retrieving help.

    Unlike the other :class:`EscCommand`\ s, each :class:`EscBuiltin` has its
    own subclass rather than its own instance, as they each need special
    behaviors. The subclasses are defined in the
    :mod:`builtin_stubs <esc.builtin_stubs>` module.

    Subclasses should override the docstring
    and the :meth:`simulated_result` method.

    Subclasses should also define :attr:`key <esc.commands.EscCommand.key>`
    and :attr:`description <esc.commands.EscCommand.description>`
    as class variables. They'll be shadowed by instance variables once we
    instantiate the class, but the values will be the same. That sounds dumb,
    but it makes sense for all other classes in the hierarchy and doesn't
    hurt us here. We don't want to define them in the ``__init__`` of each
    subclass because then we have to instantiate every class to match on them
    by key (see the reflective search in ``esc.helpme``).
    """
    def __init__(self):
        super().__init__(self.key, self.description)
        self.is_menu = False

    def execute(self, access_key, ss, registry):  # pylint: disable=useless-return
        "Executing a builtin does nothing."

    def simulated_result(self, ss, registry):
        "Reimplemented by each subclass."
        raise NotImplementedError

    def test(self):
        "Testing a builtin with esc's function test feature does nothing."

    @property
    def signature_info(self):
        "Constant string that describes the built-in as a built-in."
        type_ = f"    Type: Built-in (performs special esc actions)"
        return (type_,)


### Main menu ###
# As I write this, if the user ever sees this docstring, something's probably
# gone wrong, since there's no way to choose the main menu from a menu and thus
# get its help, but in the interest of future-proofing, we'll say something
# interesting.
MAIN_DOC = """
    The main menu. All other esc functions and menus are eventually accessible
    from this menu.
"""

# We have to define the main menu somewhere so we can get at the operations and
# menus on it. Files of functions will ultimately need to import this menu to
# register anything useful.
main_menu = EscMenu('', "Main Menu", doc=MAIN_DOC)  # pylint: disable=invalid-name


### Constructor/registration functions ###
def Menu(key, description, parent, doc, mode_display=None):  # pylint: disable=invalid-name
    """
    Register a new submenu of an existing menu.

    :param key: The keyboard key used to select this menu from its parent.
    :param description: A short description of this menu to show beside the key.
    :param parent:
        An :class:`EscMenu` to add this menu to.
        This may be ``esc.commands.main_menu`` or another menu.
    :param doc:
        A string describing the menu, to be used in the help system.
        This should be something like the docstring
        of an operation function.
    :param mode_display:
        An optional callable returning a string whose value will be shown
        beneath the name of the menu when the menu is open.
        Ordinarily, this is used to show the current value of any modes
        that apply to the functions on the menu.

    :return: A new :class:`EscMenu`.
    """
    menu = EscMenu(key, description, doc, mode_display)
    parent.register_child(menu)
    return menu


def Constant(value, key, description, menu):  # pylint: disable=invalid-name
    """
    Register a new constant. Constants are just exceedingly boring operations
    that pop no values and push a constant value,
    so this is merely syntactic sugar.

    :param value: The value of the constant,
                  as a Decimal or a value that can be converted to one.
    :param key: The key to press to select the constant from the menu.
    :param description: A brief description to show next to the *key*.
    :param menu: A :class:`Menu <EscMenu>` to place this function on.
    """
    @Operation(key=key, menu=menu, push=1, description=description,
               log_as=f"insert constant {description}")
    def func():
        return value
    # You can't define a dynamic docstring from within the function.
    func.__doc__ = f"Add the constant {description} = {value} to the stack."


def Operation(key, menu, push, description=None, retain=False, log_as=None, simulate=True):  # pylint: disable=invalid-name
    """
    Decorator to register a function on a menu
    and make it available for use as an esc operation.

    :param key:
        The key on the keyboard to press
        to trigger this operation on the menu.
    :param menu:
        The :class:`Menu <EscMenu>` to place this operation on.
        The simplest choice is ``main_menu``,
        which you can import from :mod:``esc.commands``.
    :param push:
        The number of items the decorated function
        will return to the stack on success.
        ``0`` means nothing is ever returned;
        ``-1`` means a variable number of things are returned.
    :param description:
        A very brief description of the operation this function implements,
        to be displayed next to it on the menu.
        If this is ``None`` (the default), the operation is "anonymous"
        and will be displayed at the top of the menu with just its *key*.
    :param retain:
        If ``True``, the items bound to this function's arguments
        will remain on the stack on successful execution.
        The default is ``False``
        (meaning the function's return value replaces
        whatever was there before --
        the usual behavior of an RPN calculator).
    :param log_as:
        A specification describing what appears
        in the :guilabel:`History` window after executing this function.
        It may be ``None`` (the default), ``UNOP`` or ``BINOP``,
        a .format() string, or a callable.

        * If it is ``None``, the *description* is used.

        * If it is the module constant ``esc.commands.UNOP``
          or ``esc.commands.BINOP``,
          the log string is a default suitable
          for many unary or binary operations:
          for ``UNOP`` it is
          :samp:`{description} {argument} = {return}`
          and for ``BINOP`` it is
          :samp:`{argument} {key} {argument} = {return}`.

          .. note::
            If the function being decorated does not take one or two arguments,
            respectively,
            using ``UNOP`` or ``BINOP`` will raise a
            :class:`ProgrammingError <esc.oops.ProgrammingError>`.

        * If it is a format string, positional placeholders are replaced
          with the parameters to the function in sequence,
          then the return values.
          Thus, a function with two arguments ``bos`` and ``sos``
          returning a tuple of two values replaces
          ``{0}`` with ``bos``, ``{1}`` with ``sos``,
          and ``{2}`` and ``{3}`` with the two return values.

        * If it is a callable, the parameters will be examined and bound
          by name to the following (none of these parameters are required,
          but arguments other than these will raise a
          :class:`ProgrammingError <esc.oops.ProgrammingError>`).

          :args: a list of the arguments the function requested
          :retval: a list of values the function returned
          :registry: the current :class:`Registry <esc.registers.Registry>` instance

          The function should return an appropriate string.
    :param simulate:
        If ``True`` (the default), function execution will be simulated
        when the user looks at the help page for the function,
        so they can see what would happen to the stack
        if they actually chose the function.
        You should disable this option
        if your function is extremely slow or has side effects
        (e.g., changing the system clipboard, editing registers).

    In addition to placing the function on the menu,
    the function is wrapped with the following magic.

    1. Function parameters are bound according to the following rules:

       * Most parameters are bound
         to a slice of values at the bottom of the stack, by position.
         If the function has one parameter,
         it receives :ref:`bos <Terminology and notation>`;
         if the function has two parameters,
         the first receives sos and the second bos;
         and so on.
         The parameters can have any names (see exceptions below).
         Using ``bos`` and ``sos`` is conventional for general operations,
         but if the operation is implementing some kind of formula,
         it may be more useful to name the parameters
         for their meaning in the formula.

       * By default, passed parameters are of type `Decimal`_.
         If the parameter name ends with ``_str``,
         it instead receives a string representation
         (this is exactly what shows up in the calculator window,
         so it's helpful when doing something display-oriented
         like copying to the clipboard).
         If the parameter name ends with ``_stackitem``,
         it receives the complete :class:`StackItem <esc.stack.StackItem>`,
         containing both of those representations and a few other things besides.

       * A varargs parameter, like ``*args``,
         receives the entire contents of the stack as a tuple.
         This is invalid with any other parameters except ``registry``.
         The ``_str`` and ``_stackitem`` suffixes still work.
         Again, it can have any name; ``*stack`` is conventional for esc operations.

       * The special parameter name ``registry``
         receives a :class:`Registry <esc.registers.Registry>` instance
         containing the current state of all registers.
         Using this parameter is generally discouraged;
         see :ref:`Registry` for details.

       * The special parameter name ``testing``
         receives a boolean describing whether the current execution is a test
         (see :func:`esc.functest.TestCase`).
         This can be useful if your function has side effects
         that you don't want to execute during testing,
         but you'd still like to test the rest of the function.

    2. The function has a callable attached to it as an attribute,
       called ``ensure``, which can be used to test the function at startup
       to ensure the function never stops calculating the correct answers
       due to updates or other issues:

       .. code-block:: python

            def add(sos, bos):
                return sos + bos
            add.ensure(before=[1, 2, 3], after=[1, 5])

       See :class:`TestCase <esc.functest.TestCase>`
       for further information on this testing feature.
    """
    def function_decorator(func):
        sig = signature(func)
        parms = sig.parameters.values()

        bind_all = [i for i in parms if i.kind == Parameter.VAR_POSITIONAL]
        stack_parms = [i for i in parms if i.name not in ('registry', 'testing')]
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
            if 'testing' in (i.name for i in parms):
                keyword_binding['testing'] = consts.TESTING
            return func(*positional_binding, **keyword_binding)

        # Add test definition functionality.
        def ensure(before, after=None, raises=None, close=False):
            tc = TestCase(before, after, raises, close)
            wrapper.tests.append(tc)
        wrapper.ensure = ensure
        wrapper.tests = []

        # Create a new EscOperation instance and place it on the menu.
        op = EscOperation(key=key, func=wrapper, pop=pop, push=push,
                          description=description, menu=menu, log_as=log_as,
                          retain=retain, simulate=simulate)
        menu.register_child(op)

        # Return the wrapped function to functions.py to complete
        # the decorator protocol.
        return wrapper

    return function_decorator


def Mode(name, default_value, allowable_values=None):  # pylint: disable=invalid-name
    """
    Register a new mode.

    :param name:
        The name of the mode. This is used to refer to it in code.
        If a mode with this name already exists,
        a :class:`ProgrammingError <esc.oops.ProgrammingError>` will be raised.
    :param default_value: The value the mode starts at.
    :param allowable_values:
        An optional sequence of possible values for the mode.
        If defined, if code ever tries to set a different value,
        a :class:`ProgrammingError <esc.oops.ProgrammingError>` will be raised.
    """
    return modes.register(name, default_value, allowable_values)


def ModeChange(key, description, menu, mode_name, to_value):  # pylint: disable=invalid-name
    """
    Create a new mode change operation the user can select from a menu.
    Syntactic sugar for registering an operation.

    :param key: The key to press to select the constant from the menu.
    :param description: A brief description to show next to the *key*.
    :param menu: A :class:`Menu <EscMenu>` to place this operation on.
    :param mode_name: The name of the mode, registered with :func:`Mode`,
                      to set.
    :param to_value: The value the mode will be set to
                     when this operation is selected.
    """
    op = EscOperation(key=key, func=lambda _, __: modes.set(mode_name, to_value),
                      pop=0, push=0, description=description, menu=menu)
    menu.register_child(op)
