import copy
import math
from main import STACKDEPTH

#TODO: Possibility to provide one's own error wrapper function (for instance, for '-' with zero/one item on stack?)

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
        self.menus = None
        self.curMenu = None
        self.MAX_TEXT_FUNCTIONS = STACKDEPTH

    def enterMenu(self, menu):
        "Change state to specify we are in a different menu."
        assert menu in self.menuNames.values(), \
                "Menu does not exist! Did you buildMenus()?"
        self.curMenu = menu
    def leaveMenu(self):
        "Change state to leave menu, if any."
        self.curMenu = None

    def buildMenus(self):
        # build dict of all menus in existence
        menuList = []
        for f in self.fnattrs:
            if self.fnattrs[f]['menu'] not in menuList:
                menuList.append(self.fnattrs[f]['menu'])
        self.menus = {i: [] for i in menuList}

        for f in self.functions:
            self.menus[self.fnattrs[f]['menu']].append(f)

        for i in self.menus:
            if i is not None:
                assert i in self.menuNames.values(), \
                        "I don't know about menu %s! Did you registerMenu()?" % i

        #TODO: check for dupes and assert errors

    def registerMenu(self, commandChar, name, parent=None):
        pass



    def registerFunction(self, fn, numPop, numPush, commandChar,
            commandDescr=None, menu=None):
        assert commandChar not in self.functions, \
                "Command character already used!"
        #assert self.MAX_TEXT_FUNCTIONS > len(self.functions) + 1, \
        #        "Can't fit any more functions on this screen! Try using a menu."

        if menu:
            commandChar = menu + commandChar

        self.functions.append(commandChar)
        self.fnattrs[commandChar] = {'fn': fn, 'pop': numPop, 'push': numPush,
                                     'descr': commandDescr, 'menu': menu}

    def runFunction(self, commandChar, ss):
        """
        Run the function indicated by /commandChar/, modifying the stack /ss/.
        If the function completes successfully (i.e., it did not return None),
        return True; else, write an appropriate error message to the status bar
        and return False.
        """

        if self.curMenu:
            commandChar = self.curMenu + commandChar

        if commandChar not in self.functions:
            # write an error message
            return False

        # if currently entering a number, finish that entry so we can use it
        ss.enterNumber()

        #TODO: run a wrapper to make sure there are enough elements to pop and
        #      enough space to push the results

        if self.fnattrs[commandChar]['pop'] == -1:
            # pop the whole stack; will push the whole stack back later
            args = ss.s
            ss.clearStack()
        else:
            args = ss.pop(num=self.fnattrs[commandChar]['pop'])

        retvals = self.fnattrs[commandChar]['fn'](args)
        if hasattr(retvals, 'startswith') and retvals.startswith('err'):
            return False

        # push return vals, creating an iterable from single retvals
        if self.fnattrs[commandChar]['push'] > 0:
            try:
                ss.push(retvals)
            except TypeError:
                ss.push((retvals,))
        return True

fm = FunctionManager()

# basic operations
fm.registerFunction(lambda s: s[1] + s[0], 2, 1, '+')
fm.registerFunction(lambda s: s[1] - s[0], 2, 1, '-')
fm.registerFunction(lambda s: s[1] * s[0], 2, 1, '*')
fm.registerFunction(lambda s: s[1] / s[0], 2, 1, '/')
fm.registerFunction(lambda s: s[1] ** s[0], 2, 1, '^')
fm.registerFunction(lambda s: s[1] % s[0], 2, 1, '%')
fm.registerFunction(lambda s: math.sqrt(s[0]), 1, 1, 's')

# stack operations
fm.registerFunction(lambda s: (s[0], s[0]), 1, 2, 'd', 'duplicate bos', 'q')
fm.registerFunction(lambda s: (s[0], s[1]), 2, 2, 'x', 'exchange bos, sos')
fm.registerFunction(lambda s: None, 1, 0, 'p', 'pop off bos')
fm.registerFunction(lambda s: None, -1, 0, 'c', 'clear stack')
fm.registerFunction(lambda s: [i.value for i in s[1:]], -1, 0, 'r', 'roll off tos')

#fm.registerMenu(
#fm.buildMenus()

print fm.functions
print fm.fnattrs