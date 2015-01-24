from functionmanagement import fm, modes
from main import ftostr
import display
import math

####### BEGINNING OF FUNCTIONS #######

# basic operations
fm.registerFunction(lambda s: s[1] + s[0], 2, 1, '+')
fm.registerFunction(lambda s: s[1] - s[0], 2, 1, '-')
fm.registerFunction(lambda s: s[1] * s[0], 2, 1, '*')
fm.registerFunction(lambda s: s[1] / s[0], 2, 1, '/')
fm.registerFunction(lambda s: s[1] ** s[0], 2, 1, '^')
fm.registerFunction(lambda s: s[1] % s[0], 2, 1, '%')
fm.registerFunction(lambda s: math.sqrt(s[0]), 1, 1, 's')

# stack operations
fm.registerFunction(lambda s: (s[0], s[0]), 1, 2, 'd', 'duplicate bos')
fm.registerFunction(lambda s: (s[1], s[0]), 2, 2, 'x', 'exchange bos, sos')
fm.registerFunction(lambda s: None, 1, 0, 'p', 'pop off bos')
fm.registerFunction(lambda s: [i.value for i in s[1:]], -1, 0, 'r', 'roll off tos')
fm.registerFunction(lambda s: None, -1, 0, 'c', 'clear stack')


##################
# TRIG FUNCTIONS #
##################

fm.registerMenu('t', 'trig menu', dynDisp=lambda: 'trig [%s]' % modes.trigMode)
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
