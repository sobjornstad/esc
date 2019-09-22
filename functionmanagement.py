from collections import OrderedDict
import copy
import decimal

from consts import STACKDEPTH, QUIT_CHARACTER, CONSTANT_MENU_CHARACTER
from display import screen
import modes
from oops import NotInMenuError, ProgrammingError, FunctionExecutionError


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

    # pylint: disable=unused-argument
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

    def find_menu(self, key_sequence, remaining_keys=None):
        """
        Recursively get a menu object by the key sequence leading to it.
        """
        if remaining_keys is None:
            remaining_keys = key_sequence

        if len(remaining_keys) == 1:
            if self.key != remaining_keys[0]:
                raise NotInMenuError(
                    f"The key sequence {key_sequence} does not lead to a menu.")
            else:
                return self
        else:
            return self.find_menu(remaining_keys[1:])


class EscOperation(EscFunction):
    def __init__(self, key, func, pop, push, description, menu):
        super().__init__(key, description)
        self.function = func
        self.pop = pop
        self.push = push
        self.parent = menu

    def __repr__(self):
        return f"<EscOperation '{self.key}': {self.description}"

    def execute(self, access_key, ss):
        checkpoint = ss.memento()
        try:
            args = self.retrieve_arguments(ss)
            try:
                retvals = self.function(args)
            except ValueError:
                # illegal operation; restore original args to stack and return
                raise FunctionExecutionError("Domain error! Stack unchanged.")
            except ZeroDivisionError:
                raise FunctionExecutionError("Sorry, division by zero is against the law.")
            self.store_results(ss, retvals)
        except Exception:
            ss.restore(checkpoint)
            raise
        return None

    def retrieve_arguments(self, ss):
        # Enter the number currently being edited, if any, stopping if it is
        # invalid.
        try:
            ss.enter_number(runningOp=self.key)
        except ValueError as e:
            raise FunctionExecutionError(str(e))

        # Make sure there will be space to push the results.
        # If requesting the whole stack, it's the function's responsibility to check.
        if not ss.has_push_space(self.push - self.pop) and self.pop != -1:
            numShort = self.push - self.pop - ss.freeStackSpaces
            spaces = 'space' if numShort == 1 else 'spaces'
            msg = f"'{self.key}': stack is too full (short {numShort} {spaces}."
            raise FunctionExecutionError(msg)

        if self.pop == -1:
            # Whole stack requested; will push the whole stack back later.
            args = copy.deepcopy(ss.s)
            ss.clear()
        else:
            args = ss.pop(self.pop)
            if (not args) and self.pop != 0:
                pops = 'item' if self.pop == 1 else 'items'
                msg = f"'{self.key}' needs at least {self.pop} {pops} on stack."
                raise FunctionExecutionError(msg)

        return args

    def store_results(self, ss, return_values):
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

            ss.push(coerced_retvals)


### Constructor/registration functions to be used in functions.py ###
def Menu(key, description, parent):
    "Create a new menu under the existing menu /parent/."
    menu = EscMenu(key, description)
    parent.register_child(menu)
    return menu


main_menu = EscMenu('', "Main Menu")


def Constant(value, key, description, menu):
    "Create a new constant. Syntactic sugar for registering a function."
    op = EscOperation(key=key, func=lambda _: value, pop=0, push=1,
                      description=description, menu=menu)
    menu.register_child(op)


def Function(key, menu, push, pop, description=None):
    """
    Decorator to register a function on a given menu.
    """
    def function_decorator(func):
        op = EscOperation(key=key, func=func, pop=pop, push=push,
                          description=description, menu=menu)
        menu.register_child(op)
        return func
    return function_decorator


def Mode(name, default_value, allowable_values=None):
    return modes.register(name, default_value, allowable_values)


def ModeChange(key, description, menu, mode_name, to_value):
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

    MIN_XPOSN = 2
    MAX_XPOSN = 22
    xposn = 2
    yposn = 1

    # Print menu title.
    if not menu.is_main_menu:
        screen().add_menu(menu.description, yposn, xposn-1)
        yposn += 1

    # Print anonymous functions to the screen.
    for i in menu.anonymous_children:
        screen().add_command(i.key, None, yposn, xposn)
        xposn += 2
        if xposn >= MAX_XPOSN - 2:
            yposn += 1
            xposn = MIN_XPOSN

    # Now normal functions and menus.
    yposn += 1
    xposn = MIN_XPOSN
    for i in menu.named_children:
        screen().add_command(i.key, i.description, yposn, xposn)
        yposn += 1

    # then the undo option, if on the main menu
    if menu.is_main_menu:
        screen().add_command('u', 'undo (', yposn, xposn)
        screen().add_command('^r', 'redo)', yposn, xposn + 8)
        yposn += 1

    # then the quit option, which is always there but is not a function
    quitName = 'quit' if menu.is_main_menu else 'cancel'
    screen().add_command(QUIT_CHARACTER, quitName, yposn, xposn)

    # finally, make curses figure out how it's supposed to draw this
    screen().commandsw.refresh()



class FunctionManager(object):
    """
    This object maintains the list of available functions / commands, handles
    providing menus for them, and runs them on demand.
    """
    def __init__(self):
        # consider passing in a status bar write object
        self.functions = []
        self.fnattrs = {}
        self.menuNames = {}
        self.menuFns = {}
        self.curMenu = None
        self.quitAfter = False
        self.statusDisplayRequested = False
        self.MAX_TEXT_FUNCTIONS = STACKDEPTH

    def setStatusDisplayRequested(self):
        """
        Indicate that, although there was no error, we wish to display something
        on the status bar. This function is a setter for an attribute which is
        initialized to False every time a function is run. If the attribute is
        set at the end of runFunction, we will return False even though the
        operation was a success, indicating something needs to be displayed.
        """
        self.statusDisplayRequested = True


    ##### Menu handling ######
    def enterMenu(self, menu):
        "Change state to specify we are in a different menu."
        self.curMenu = menu
        if menu == CONSTANT_MENU_CHARACTER:
            msg = "Expecting constant choice (q to cancel)"
        else:
            msg = "Expecting %s command (q to cancel)" % self.menuNames[menu]

        self.displayMenu()
        screen().set_status_msg(msg)

    def leaveMenu(self):
        "Change state and display to leave menu, if any."
        if self.curMenu:
            self.curMenu = None
            self.displayMenu()

    def registerMenu(self, commandChar, name, dynDisp=None):
        "Create a new menu. Must be done before adding items to it."
        self.menuNames[commandChar] = name
        self.functions.append(commandChar)
        self.fnattrs[commandChar] = '@menu'
        if dynDisp:
            self.menuFns[commandChar] = dynDisp

    def displayMenu(self):
        """
        Update the commands window to show the current menu.
        """

        screen().reset_commands_window()

        MIN_XPOSN = 2
        MAX_XPOSN = 22
        xposn = 2
        yposn = 1
        anonFunctions = []
        normFunctions = []
        for i in self.functions:
            # menu?
            try:
                menu = self.fnattrs[i] == '@menu'
            except TypeError:
                pass
            else:
                if menu:
                    normFunctions.append(i)
                    continue

            # anonymous function?
            if not self.fnattrs[i]['descr']:
                anonFunctions.append(i)
                continue

            # normal function.
            normFunctions.append(i)

        # filter out anything not in the current menu
        for i in anonFunctions[:]:
            if (len(i) > 1 and self.curMenu != i[0]) or \
                    (len(i) == 1 and self.curMenu):
                anonFunctions.remove(i)

        for i in normFunctions[:]:
            if (len(i) > 1 and self.curMenu != i[0]) or \
                    (len(i) == 1 and self.curMenu):
                normFunctions.remove(i)

        # print menu title, using menuFns if available
        if self.curMenu in self.menuFns:
            screen().add_menu(self.menuFns[self.curMenu](), yposn, xposn-1)
            yposn += 1
        elif self.curMenu:
            screen().add_menu(self.menuNames[self.curMenu], yposn, xposn-1)
            yposn += 1


        # print anonymous functions to the screen
        for i in anonFunctions:
            screen().add_command(i, None, yposn, xposn)
            xposn += 2
            if xposn >= MAX_XPOSN - 2:
                yposn += 1
                xposn = MIN_XPOSN

        # then normal functions and menus
        yposn += 1
        xposn = MIN_XPOSN
        for i in normFunctions:
            dispChar = i if not self.curMenu else i[1] # remove menu char
            try:
                screen().add_command(dispChar, self.fnattrs[i]['descr'], yposn, xposn)
            except TypeError: # menu
                screen().add_command(dispChar, self.menuNames[i], yposn, xposn)
            yposn += 1

        # then the undo option, if on the main menu
        if not self.curMenu:
            screen().add_command('u', 'undo (', yposn, xposn)
            screen().add_command('^r', 'redo)', yposn, xposn + 8)
            yposn += 1

        # then the quit option, which is always there but is not a function
        quitName = 'cancel' if self.curMenu else 'quit'
        screen().add_command(QUIT_CHARACTER, quitName, yposn, xposn)

        # finally, make curses figure out how it's supposed to draw this
        screen().commandsw.refresh()


    ##### Function registration and use #####
    def registerFunction(self, fn, numPop, numPush, commandChar,
                         commandDescr=None, menu=None):
        if menu:
            assert menu in self.menuNames, \
                    "That menu doesn't exist (try registerMenu())."
            commandChar = menu + commandChar

        assert commandChar not in self.functions, \
                "Command character already used!"
        #assert self.MAX_TEXT_FUNCTIONS > len(self.functions) + 1, \
        #        "Can't fit any more functions on this screen! Try using a menu."

        self.functions.append(commandChar)
        self.fnattrs[commandChar] = {'fn': fn, 'pop': numPop, 'push': numPush,
                                     'descr': commandDescr, 'menu': menu}

    def registerModeChange(self, fn, commandChar, commandDescr, menu):
        self.registerFunction(fn, 0, 0, commandChar, commandDescr, menu)

    def registerConstant(self, cst, commandChar, commandDescr,
                         menu=CONSTANT_MENU_CHARACTER):
        """
        Constants are handled as functions which pop zero values off the stack
        and push one (predefined) value onto the stack. This function creates
        such a function given the predefined value, and places it onto the
        constants menu under /commandChar/ and name /commandDescr/.
        Alternatively, you can specify a different menu.
        """

        # silently register the constant menu if it isn't already
        cmc = CONSTANT_MENU_CHARACTER
        if menu == cmc and cmc not in self.menuNames:
            self.registerMenu(cmc, "insert constant")

        self.registerFunction(lambda discard: cst, 0, 1,
                              commandChar, commandDescr, menu)

    def runFunction(self, commandChar, ss):
        """
        Run the function indicated by /commandChar/, modifying the stack /ss/.
        If the function exits silently (i.e., it did not return None and did
        not request a status bar display by doing a
        setStatusDisplayRequested()), return True; else, write an appropriate
        message to the status bar and return False.
        """

        self.statusDisplayRequested = False # see docstring of setter

        if commandChar == QUIT_CHARACTER:
            if self.curMenu:
                self.leaveMenu()
            else:
                # in main menu; quit at end of main loop
                self.quitAfter = True
            return True

        if self.curMenu:
            commandChar = self.curMenu + commandChar
            self.leaveMenu() # after using a function from a menu, close it

        if commandChar not in self.functions:
            screen().set_status_msg("Unrecognized command '%s'." % commandChar)
            return False

        if self.fnattrs[commandChar] == '@menu':
            self.enterMenu(commandChar)
            return False # False because we need to display a status item

        # define the name of this function in case we need to communicate it
        if self.fnattrs[commandChar]['descr']:
            fnName = self.fnattrs[commandChar]['descr']
        else:
            fnName = commandChar

        # If all of those passed, we're going to run an operation, so enter the
        # number currently being edited, if any, stopping if it is invalid.
        # Note that this also checkpoints the state of the stack for us.
        try:
            ss.enter_number(fnName)
        except ValueError as e:
            screen().set_status_msg(str(e))
            return False

        # make sure there will be space to push the results
        # if requesting the whole stack, it's function's responsibility to check
        numToPop = self.fnattrs[commandChar]['pop']
        numToPush = self.fnattrs[commandChar]['push']
        if not ss.has_push_space(numToPush - numToPop) and numToPop != -1:
            msg = "'%s': stack is too full (short %i space%s)."
            numShort = numToPush - numToPop - ss.freeStackSpaces
            msg = msg % (fnName, numShort, 's' if numShort != 1 else '')
            screen().set_status_msg(msg)
            return False

        if numToPop == -1:
            # whole stack requested; will push the whole stack back later
            sr = copy.deepcopy(ss.s)
            sr.reverse()
            args = sr
            ss.clear()
        else:
            #print ss.s
            args = ss.pop(numToPop)
            if (not args) and numToPop != 0:
                msg = '"%s" needs at least %i item%s on stack.'
                msg = msg % (fnName, numToPop, 's' if numToPop != 1 else '')
                screen().set_status_msg(msg)
                return False

        try:
            retvals = self.fnattrs[commandChar]['fn'](args)
        except ValueError:
            # illegal operation; restore original args to stack and return
            ss.push(args)
            screen().set_status_msg("Domain error! Stack unchanged.")
            return False
        except ZeroDivisionError:
            ss.push(args)
            screen().set_status_msg("Sorry, division by zero is against the law.")
            return False


        if hasattr(retvals, 'startswith') and retvals.startswith('err: '):
            screen().set_status_msg(retvals[5:])
            return False

        # push return vals, creating an iterable from single retvals
        if numToPush > 0 or (numToPop == -1 and retvals is not None):
            if not hasattr(retvals, '__iter__'):
                retvals = (retvals,)

            coerced_retvals = []
            for i in retvals:
                # It's legal for functions to return data types that can be converted
                # to Decimal.
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

            ss.push(coerced_retvals)
        return True if not self.statusDisplayRequested else False


# global module objects
#fm = FunctionManager()
#modes = ModeStorage()
