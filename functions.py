from main import STACKDEPTH
from time import sleep #DEBUG

class FunctionManager(object):
    """
    This object maintains the list of available functions / commands and runs
    them on demand.
    """

    def __init__(self):
        self.functions = {}
        self.params = {}
        self.MAX_TEXT_FUNCTIONS = STACKDEPTH

    def registerFunction(self, fn, numPop, numPush, commandChar, commandDescr=None):
        assert commandChar not in self.functions, \
                "Command character already used!"
        assert self.MAX_TEXT_FUNCTIONS > len(self.functions) + 1, \
                "Can't fit any more functions on this screen! Try using a menu."

        self.functions[commandChar] = fn
        self.params[commandChar] = {'pop': numPop, 'push': numPush,
                                    'descr': commandDescr}

    def runFunction(self, commandChar, ss):
        if commandChar not in self.functions:
            return False

        args = ss.pop(num=self.params[commandChar]['pop'])
        retvals = self.functions[commandChar](args)
        try:
            # assume multiple return values
            ss.push(retvals)
        except TypeError:
            # there was only one return value; make a one-element iterable
            ss.push((retvals,))

        return True

fm = FunctionManager()

def plusFn(s):
    return s[1] + s[0]

fm.registerFunction(plusFn, 2, 1, '+')
