from decimal import Decimal
import math

from display import screen
from functionmanagement import function, constant, main_menu, Menu


####################
# BASIC OPERATIONS #
####################

@function('+', menu=main_menu, pop=2, push=1)
def add(s):
    return s[0] + s[1]

@function('-', menu=main_menu, pop=2, push=1)
def subtract(s):
    return s[0] - s[1]

@function('*', menu=main_menu, pop=2, push=1)
def multiply(s):
    return s[0] * s[1]

@function('/', menu=main_menu, pop=2, push=1)
def divide(s):
    return s[0] / s[1]

@function('^', menu=main_menu, pop=2, push=1)
def exponentiate(s):
    return s[0] ** s[1]

@function('%', menu=main_menu, pop=2, push=1)
def modulus(s):
    return s[0] * s[1]

@function('s', menu=main_menu, pop=1, push=1)
def modulus(s):
    return math.sqrt(s[0])


####################
# STACK OPERATIONS #
####################

@function('d', menu=main_menu, pop=1, push=2, description='duplicate bos')
def duplicate(s):
    return s[0], s[0]

@function('x', menu=main_menu, pop=2, push=2, description='exchange bos, sos')
def exchange(s):
    return s[1], s[0]

@function('p', menu=main_menu, pop=1, push=0, description='pop off bos')
def pop(s):
    return None

@function('r', menu=main_menu, pop=-1, push=-1, description='roll off tos')
def roll(s):
    return [i.decimal for i in s[1:]]

@function('c', menu=main_menu, pop=-1, push=0, description='clear stack')
def clear(s):
    return None


###################
## TRIG FUNCTIONS #
###################

trig_menu = Menu('t', 'trig menu')
main_menu.register_child(trig_menu)
#def trigWrapper(s, func, arc=False):
#    """
#    Used anytime a trig function is called. Performs any conversions from
#    degrees to radians and vice versa, as called for by modes.trigMode (all
#    Python math module functions use only radians).
#
#    Takes the requested stack item, a function to be called on the value
#    after/before the appropriate conversion, and a boolean indicating whether
#    this is an arc/inverse function (requiring radian->degree after
#    computation) or a forward one (requiring degree->radian before
#    computation).
#
#    Returns the new value of the stack as passed out by the provided function,
#    after possible conversion to degrees.
#    """
#
#    bos = s[0]
#
#    # orig had 'ss and': not sure why that was necessary; probably isn't here
#    if modes.trigMode == 'degrees' and not arc:
#        bos = math.radians(bos)
#    ret = func(bos)
#    if modes.trigMode == 'degrees' and arc:
#        ret = math.degrees(ret)
#    return ret
#
#fm.registerFunction(lambda s: trigWrapper(s, math.sin), 1, 1, 's', 'sine', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.cos), 1, 1, 'c', 'cosine', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.tan), 1, 1, 't', 'tangent', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.asin, True),
#                    1, 1, 'i', 'arc sin', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.acos, True),
#                    1, 1, 'o', 'arc cos', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.atan, True),
#                    1, 1, 'a', 'arc tan', 't')
#
#def toDegrees(_):
#    modes.trigMode = 'degrees'
#def toRadians(_):
#    modes.trigMode = 'radians'
#fm.registerModeChange(toDegrees, 'd', 'degree mode', 't')
#fm.registerModeChange(toRadians, 'r', 'radian mode', 't')

#fm.registerMenu('t', 'trig menu', dynDisp=lambda: 'trig [%s]' % modes.trigMode)
#def trigWrapper(s, func, arc=False):
#    """
#    Used anytime a trig function is called. Performs any conversions from
#    degrees to radians and vice versa, as called for by modes.trigMode (all
#    Python math module functions use only radians).
#
#    Takes the requested stack item, a function to be called on the value
#    after/before the appropriate conversion, and a boolean indicating whether
#    this is an arc/inverse function (requiring radian->degree after
#    computation) or a forward one (requiring degree->radian before
#    computation).
#
#    Returns the new value of the stack as passed out by the provided function,
#    after possible conversion to degrees.
#    """
#
#    bos = s[0]
#
#    # orig had 'ss and': not sure why that was necessary; probably isn't here
#    if modes.trigMode == 'degrees' and not arc:
#        bos = math.radians(bos)
#    ret = func(bos)
#    if modes.trigMode == 'degrees' and arc:
#        ret = math.degrees(ret)
#    return ret
#
#fm.registerFunction(lambda s: trigWrapper(s, math.sin), 1, 1, 's', 'sine', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.cos), 1, 1, 'c', 'cosine', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.tan), 1, 1, 't', 'tangent', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.asin, True),
#                    1, 1, 'i', 'arc sin', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.acos, True),
#                    1, 1, 'o', 'arc cos', 't')
#fm.registerFunction(lambda s: trigWrapper(s, math.atan, True),
#                    1, 1, 'a', 'arc tan', 't')
#
#def toDegrees(_):
#    modes.trigMode = 'degrees'
#def toRadians(_):
#    modes.trigMode = 'radians'
#fm.registerModeChange(toDegrees, 'd', 'degree mode', 't')
#fm.registerModeChange(toRadians, 'r', 'radian mode', 't')


##############
# LOGARITHMS #
##############

log_menu = Menu('l', 'log menu')
main_menu.register_child(log_menu)

@function('l', menu=log_menu, pop=1, push=1, description='log x')
def log(s):
    return s[0].log10()

@function('1', menu=log_menu, pop=1, push=1, description='10^x')
def tentothex(s):
    return 10 ** s[0]

@function('n', menu=log_menu, pop=1, push=1, description='ln x')
def ln(s):
    return s[0].ln()

@function('n', menu=log_menu, pop=1, push=1, description='e^x')
def etothex(s):
    return s[0].exp()

#############
# CONSTANTS #
#############

constant(math.pi, 'p', 'pi')
constant(math.e, 'e', 'e')

# 
#################
# MISCELLANEOUS #
#################

@function('y', menu=main_menu, pop=1, push=1, description='yank bos to cboard')
def yankBos(s):
    """
    Use xsel to yank bottom of stack. This probably only works on Unix-like
    systems.
    """
    # help from: http://stackoverflow.com/questions/7606062/
    # is-there-a-way-to-directly-send-a-python-output-to-clipboard
    from subprocess import Popen, PIPE
    p = Popen(['xsel', '-bi'], stdin=PIPE)
    p.communicate(input=str(s[0]).encode())
    screen().set_status_msg('"%s" placed on system clipboard.' % str(s[0]))
    #FIXME: disabled
    #fm.setStatusDisplayRequested()
    return s[0] # put back onto stack

@function('T', menu=main_menu, pop=1, push=1, description='add MN sales tax')
def addMnSalesTax(s):
    tax = Decimal(.07375) * s[0]
    return s[0] + tax



##TODO:
# Get constants menu to display in the right spot
# Reenable trig menu and modes
# Reenable setStatusDisplayRequested() but do it in a cleaner way than before
# Clean up all the old functionmanager crap no longer needed
# Avoid circular dependency?
# Menus should have a description for the status bar