import math
from main import STACKDEPTH, ftostr
import display
from time import sleep #debug

#TODO: Possibility to provide one's own error wrapper function (for instance, for '-' with zero/one item on stack?)

QUIT_CHARACTER = 'q'
CONSTANT_MENU_CHARACTER = 'i'

class ModeStorage(object):
    """
    This object allows you to store static variables (or calculator "modes").
    It is instantiated in the functions file as 'modes' and can be modified by
    a function. It has no methods; simply assign to any attributes that are not
    being used by another function. If there should be a default value, you can
    add it to __init__.
    """

    def __init__(self):
        self.trigMode = 'degrees'

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
        self.curMenu = None
        self.quitAfter = False
        self.MAX_TEXT_FUNCTIONS = STACKDEPTH

    def enterMenu(self, menu):
        "Change state to specify we are in a different menu."
        assert menu in self.menuNames, \
                "Menu does not exist! Did you buildMenus()?"
        self.curMenu = menu
        if menu == CONSTANT_MENU_CHARACTER:
            msg = "Expecting constant choice (q to cancel)"
        else:
            msg = "Expecting %s command (q to cancel)" % self.menuNames[menu]

        self.displayMenu()
        display.changeStatusMsg(msg)


    def leaveMenu(self):
        "Change state and display to leave menu, if any."
        if self.curMenu:
            self.curMenu = None
            self.displayMenu()

    def registerMenu(self, commandChar, name):
        self.menuNames[commandChar] = name
        self.functions.append(commandChar)
        self.fnattrs[commandChar] = '@menu'

    def displayMenu(self):
        """
        Update the commands window to show the current menu.
        """

        display.resetCommandsWindow()

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

        # print anonymous functions to the screen
        for i in anonFunctions:
            display.addCommand(i, None, yposn, xposn)
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
                display.addCommand(dispChar, self.fnattrs[i]['descr'], yposn, xposn)
            except TypeError: # menu
                display.addCommand(dispChar, self.menuNames[i], yposn, xposn)
            yposn += 1

        # then the quit option, which is always there but is not a function
        quitName = 'cancel' if self.curMenu else 'quit'
        display.addCommand('q', quitName, yposn, xposn)


        # finally, make curses figure out how it's supposed to draw this
        display.commandsw.refresh()


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

    def setStatusDisplayRequested(self):
        """
        Indicate that, although there was no error, we wish to display something
        on the status bar. This function is a setter for an attribute which is
        initialized to False every time a function is run. If the attribute is
        set at the end of runFunction, we will return False even though the
        operation was a success, indicating something needs to be displayed.
        """
        self.statusDisplayRequested = True


    def runFunction(self, commandChar, ss):
        """
        Run the function indicated by /commandChar/, modifying the stack /ss/.
        If the function completes successfully (i.e., it did not return None),
        return True; else, write an appropriate error message to the status bar
        and return False.
        """

        self.statusDisplayRequested = False # see docstring for setter

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
            display.changeStatusMsg("Unrecognized command '%s'." % commandChar)
            return False

        if self.fnattrs[commandChar] == '@menu':
            self.enterMenu(commandChar)
            return False # False because we need to display a status item

        # define the name of this function in case we need to communicate it
        if self.fnattrs[commandChar]['descr']:
            fnName = self.fnattrs[commandChar]['descr']
        else:
            fnName = commandChar

        # if all of those passed, we're going to run an operation, so enter the
        # number currently being edited, if any, stopping if it is invalid
        if ss.enterNumber(fnName) is False:
            return False

        # make sure there will be space to push the results
        # if requesting the whole stack, it's function's responsibility to check
        numToPop = self.fnattrs[commandChar]['pop']
        numToPush = self.fnattrs[commandChar]['push']
        if not ss.enoughPushSpace(numToPush - numToPop) and numToPop != -1:
            msg = "'%s': stack is too full (short %i space%s)."
            numShort = numToPush - numToPop - ss.freeStackSpaces()
            msg = msg % (fnName, numShort, 's' if numShort != 1 else '')
            display.changeStatusMsg(msg)
            return False

        if numToPop == -1:
            # whole stack requested; will push the whole stack back later
            args = ss.s #TODO: Does this get bos in the right place? No...?
            ss.clearStack()
        else:
            #print ss.s
            args = ss.pop(numToPop)
            if (not args) and numToPop != 0:
                msg = '"%s" needs at least %i item%s on stack.'
                msg = msg % (fnName, numToPop, 's' if numToPop != 1 else '')
                display.changeStatusMsg(msg)
                return False

        try:
            retvals = self.fnattrs[commandChar]['fn'](args)
        except ValueError:
            # illegal operation; restore original args to stack and return
            ss.push(args)
            display.changeStatusMsg("Domain error! Stack unchanged.")
            return False


        if hasattr(retvals, 'startswith') and retvals.startswith('err: '):
            display.changeStatusMsg(retvals[5:])
            return False

        # push return vals, creating an iterable from single retvals
        if numToPush > 0 or (numToPop == -1 and retvals is not None):
            try:
                ss.push(retvals)
            except TypeError:
                ss.push((retvals,))
        return True if not self.statusDisplayRequested else False

####### BEGINNING OF FUNCTIONS #######
# Note: eventually I anticipate this part will be in a separate file

fm = FunctionManager()
modes = ModeStorage()

# basic operations
fm.registerFunction(lambda s: s[1] + s[0], 2, 1, '+')
fm.registerFunction(lambda s: s[1] - s[0], 2, 1, '-')
fm.registerFunction(lambda s: s[1] * s[0], 2, 1, '*')
fm.registerFunction(lambda s: s[1] / s[0], 2, 1, '/')
fm.registerFunction(lambda s: s[1] ** s[0], 2, 1, '^')
fm.registerFunction(lambda s: s[1] % s[0], 2, 1, '%')
fm.registerFunction(lambda s: math.sqrt(s[0]), 1, 1, 's', 'square root')

# stack operations
fm.registerFunction(lambda s: (s[0], s[0]), 1, 2, 'd', 'duplicate bos')
fm.registerFunction(lambda s: (s[0], s[1]), 2, 2, 'x', 'exchange bos, sos')
fm.registerFunction(lambda s: None, 1, 0, 'p', 'pop off bos')
fm.registerFunction(lambda s: None, -1, 0, 'c', 'clear stack')
fm.registerFunction(lambda s: [i.value for i in s[1:]], -1, 0, 'r', 'roll off tos')


##################
# TRIG FUNCTIONS #
##################

fm.registerMenu('t', 'trig menu')
def trigWrapper(s, func, arc=False):
    """
    Used anytime a trig function is called. Performs any conversions from
    degrees to radians and vice versa, as called for by modes.trigMode (all
    Python math module functions use only radians).

    Takes the requested stack item, a function to be called on the value
    after/before the appropriate conversion, and a boolean indicating whether
    this is an arc/inverse function (requiring radian->degree after
    computation) or a forward one (requiring degree->radian before
    computation).

    Returns the new value of the stack as passed out by the provided function,
    after possible conversion to degrees.
    """

    bos = s[0]

    # orig had 'ss and': not sure why that was necessary; probably isn't here
    if modes.trigMode == 'degrees' and not arc:
        bos = math.radians(bos)
    ret = func(bos)
    if modes.trigMode == 'degrees' and arc:
        ret = math.degrees(ret)
    return ret

fm.registerFunction(lambda s: trigWrapper(s, math.sin), 1, 1, 's', 'sine', 't')
fm.registerFunction(lambda s: trigWrapper(s, math.cos), 1, 1, 'c', 'cosine', 't')
fm.registerFunction(lambda s: trigWrapper(s, math.tan), 1, 1, 't', 'tangent', 't')
fm.registerFunction(lambda s: trigWrapper(s, math.asin, True),
        1, 1, 'i', 'arc sin', 't')
fm.registerFunction(lambda s: trigWrapper(s, math.acos, True),
        1, 1, 'o', 'arc cos', 't')
fm.registerFunction(lambda s: trigWrapper(s, math.atan, True),
        1, 1, 'a', 'arc tan', 't')

def toDegrees(discard):
    modes.trigMode = 'degrees'
def toRadians(discard):
    modes.trigMode = 'radians'
fm.registerModeChange(toDegrees, 'd', 'degree mode', 't')
fm.registerModeChange(toRadians, 'r', 'radian mode', 't')


##############
# LOGARITHMS #
##############

fm.registerMenu('l', 'log menu')
fm.registerFunction(lambda s: math.log10(s[0]), 1, 1, 'l', 'log x', 'l')
fm.registerFunction(lambda s: math.pow(10, s[0]), 1, 1, '1', '10^x', 'l')
fm.registerFunction(lambda s: math.log(s[0]), 1, 1, 'n', 'ln x', 'l')
fm.registerFunction(lambda s: math.pow(math.e, s[0]), 1, 1, 'e', 'e^x', 'l')


#############
# CONSTANTS #
#############

fm.registerConstant(math.pi, 'p', 'pi')
fm.registerConstant(math.e, 'e', 'e')




# miscellaneous
def yankBos(s):
    """
    Use xsel to yank bottom of stack. This probably only works on Unix-like
    systems.
    """
    # help from: http://stackoverflow.com/questions/7606062/
    # is-there-a-way-to-directly-send-a-python-output-to-clipboard
    from subprocess import Popen, PIPE
    p = Popen(['xsel', '-bi'], stdin=PIPE)
    p.communicate(input=ftostr(s[0]))
    display.changeStatusMsg('"%s" placed on system clipboard.' % ftostr(s[0]))
    fm.setStatusDisplayRequested()
    return s[0] # put back onto stack

fm.registerFunction(yankBos, 1, 1, 'y', 'yank bos to cboard')
