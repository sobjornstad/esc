from decimal import Decimal
import math

from display import screen
from functionmanagement import Constant, Function, Menu, Mode, ModeChange, main_menu
import modes


####################
# BASIC OPERATIONS #
####################

@Function('+', menu=main_menu, pop=2, push=1)
def add(s):
    return s[0] + s[1]

@Function('-', menu=main_menu, pop=2, push=1)
def subtract(s):
    return s[0] - s[1]

@Function('*', menu=main_menu, pop=2, push=1)
def multiply(s):
    return s[0] * s[1]

@Function('/', menu=main_menu, pop=2, push=1)
def divide(s):
    return s[0] / s[1]

@Function('^', menu=main_menu, pop=2, push=1)
def exponentiate(s):
    return s[0] ** s[1]

@Function('%', menu=main_menu, pop=2, push=1)
def modulus(s):
    return s[0] * s[1]

@Function('s', menu=main_menu, pop=1, push=1)
def sqrt(s):
    return math.sqrt(s[0])


####################
# STACK OPERATIONS #
####################

@Function('d', menu=main_menu, pop=1, push=2, description='duplicate bos')
def duplicate(s):
    return s[0], s[0]

@Function('x', menu=main_menu, pop=2, push=2, description='exchange bos, sos')
def exchange(s):
    return s[1], s[0]

@Function('p', menu=main_menu, pop=1, push=0, description='pop off bos')
def pop(s):
    return None

@Function('r', menu=main_menu, pop=-1, push=-1, description='roll off tos')
def roll(s):
    return [i.decimal for i in s[1:]]

@Function('c', menu=main_menu, pop=-1, push=0, description='clear stack')
def clear(s):
    return None


###################
## TRIG FUNCTIONS #
###################

trig_menu = Menu('t', 'trig menu', parent=main_menu)

def trig_wrapper(s, func, arc=False):
    """
    Used anytime a trig Function is called. Performs any conversions from
    degrees to radians and vice versa, as called for by modes.trigMode (all
    Python math module functions use only radians).

    Takes the requested stack item, a Function to be called on the value
    after/before the appropriate conversion, and a boolean indicating whether
    this is an arc/inverse Function (requiring radian->degree after
    computation) or a forward one (requiring degree->radian before
    computation).

    Returns the new value of the stack as passed out by the provided Function,
    after possible conversion to degrees.
    """
    bos = s[0]
    if modes.get('trig_mode') == 'degrees' and not arc:
        bos = math.radians(bos)
    ret = func(bos)
    if modes.get('trig_mode') == 'degrees' and arc:
        ret = math.degrees(ret)
    return ret

@Function('s', menu=trig_menu, pop=1, push=1, description='sine')
def sine(s):
    return trig_wrapper(s, math.sin)

@Function('c', menu=trig_menu, pop=1, push=1, description='cosine')
def cosine(s):
    return trig_wrapper(s, math.cos)

@Function('t', menu=trig_menu, pop=1, push=1, description='tangent')
def tangent(s):
    return trig_wrapper(s, math.tan)

@Function('i', menu=trig_menu, pop=1, push=1, description='arc sin')
def arc_sine(s):
    return trig_wrapper(s, math.sin)

@Function('o', menu=trig_menu, pop=1, push=1, description='arc cos')
def arc_cosine(s):
    return trig_wrapper(s, math.cos)

@Function('a', menu=trig_menu, pop=1, push=1, description='arc tan')
def arc_tangent(s):
    return trig_wrapper(s, math.tan)

Mode(name='trig_mode', default_value='radians', allowable_values=('degrees', 'radians'))
ModeChange(key='d', description='degrees', menu=trig_menu, mode_name='trig_mode',
           to_value='degrees')
ModeChange(key='r', description='radians', menu=trig_menu, mode_name='trig_mode',
           to_value='radians')


##############
# LOGARITHMS #
##############

log_menu = Menu('l', 'log menu', parent=main_menu)

@Function('l', menu=log_menu, pop=1, push=1, description='log x')
def log(s):
    return s[0].log10()

@Function('1', menu=log_menu, pop=1, push=1, description='10^x')
def tentothex(s):
    return 10 ** s[0]

@Function('n', menu=log_menu, pop=1, push=1, description='ln x')
def ln(s):
    return s[0].ln()

@Function('n', menu=log_menu, pop=1, push=1, description='e^x')
def etothex(s):
    return s[0].exp()

#############
# CONSTANTS #
#############

Constant(math.pi, 'p', 'pi')
Constant(math.e, 'e', 'e')


#################
# MISCELLANEOUS #
#################

@Function('y', menu=main_menu, pop=1, push=1, description='yank bos to cboard')
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

@Function('T', menu=main_menu, pop=1, push=1, description='add MN sales tax')
def addMnSalesTax(s):
    tax = Decimal(.07375) * s[0]
    return s[0] + tax



##TODO:
# Get constants menu to display in the right spot
# Reenable setStatusDisplayRequested() but do it in a cleaner way than before
# Avoid circular dependency? (See chalkboard)
# Menus should have a description for the status bar, and should be able to display mode
# Clean up all the old functionmanager crap no longer needed