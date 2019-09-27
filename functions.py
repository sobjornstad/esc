"""
functions.py -- default calculator functions
"""

# pylint: disable=invalid-name

from decimal import Decimal
import math

from consts import CONSTANT_MENU_CHARACTER
from menus import UNOP, BINOP, Constant, Function, Menu, Mode, ModeChange, main_menu
import modes
from oops import InsufficientItemsError
import status


####################
# BASIC OPERATIONS #
####################

@Function('+', menu=main_menu, pop=2, push=1, log_as=BINOP)
def add(s):
    return s[0] + s[1]

@Function('-', menu=main_menu, pop=2, push=1, log_as=BINOP)
def subtract(s):
    return s[0] - s[1]

@Function('*', menu=main_menu, pop=2, push=1, log_as=BINOP)
def multiply(s):
    return s[0] * s[1]

@Function('/', menu=main_menu, pop=2, push=1, log_as=BINOP)
def divide(s):
    return s[0] / s[1]

@Function('^', menu=main_menu, pop=2, push=1, log_as=BINOP)
def exponentiate(s):
    return s[0] ** s[1]

@Function('%', menu=main_menu, pop=2, push=1, log_as=BINOP)
def modulus(s):
    return s[0] % s[1]

@Function('s', menu=main_menu, pop=1, push=1, log_as="sqrt {0} = {1}")
def sqrt(s):
    return math.sqrt(s[0])


####################
# STACK OPERATIONS #
####################

@Function('d', menu=main_menu, pop=1, push=2, description='duplicate bos',
          log_as="duplicate {0}")
def duplicate(s):
    return s[0], s[0]

@Function('x', menu=main_menu, pop=2, push=2, description='exchange bos, sos',
          log_as="{1} <=> {0}")
def exchange(s):
    return s[1], s[0]

@Function('p', menu=main_menu, pop=1, push=0, description='pop off bos',
          log_as="pop bos {0}")
def pop(_):
    return None

@Function('r', menu=main_menu, pop=-1, push=-1, description='roll off tos',
          log_as="roll off tos {0}")
def roll(s):
    "Remove the top item from the stack."
    if not s:
        raise InsufficientItemsError(number_required=1)
    return [i.decimal for i in s[1:]]

@Function('c', menu=main_menu, pop=-1, push=0, description='clear stack')
def clear(s):  #pylint: disable=useless-return
    "Clear all items from the stack."
    if not s:
        raise InsufficientItemsError(number_required=1)
    return None


###################
## TRIG FUNCTIONS #
###################

TRIG_MODE_NAME = 'trig_mode'
def trig_mode_display():
    return f"[{modes.get(TRIG_MODE_NAME)}]"
trig_menu = Menu('t', 'trig menu', parent=main_menu, mode_display=trig_mode_display)


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
    if modes.get(TRIG_MODE_NAME) == 'degrees' and not arc:
        bos = math.radians(bos)
    ret = func(bos)
    if modes.get(TRIG_MODE_NAME) == 'degrees' and arc:
        ret = math.degrees(ret)
    return ret

@Function('s', menu=trig_menu, pop=1, push=1, description='sine', log_as=UNOP)
def sine(s):
    return trig_wrapper(s, math.sin)

@Function('c', menu=trig_menu, pop=1, push=1, description='cosine', log_as=UNOP)
def cosine(s):
    return trig_wrapper(s, math.cos)

@Function('t', menu=trig_menu, pop=1, push=1, description='tangent', log_as=UNOP)
def tangent(s):
    return trig_wrapper(s, math.tan)

@Function('i', menu=trig_menu, pop=1, push=1, description='arc sin', log_as=UNOP)
def arc_sine(s):
    return trig_wrapper(s, math.sin)

@Function('o', menu=trig_menu, pop=1, push=1, description='arc cos', log_as=UNOP)
def arc_cosine(s):
    return trig_wrapper(s, math.cos)

@Function('a', menu=trig_menu, pop=1, push=1, description='arc tan', log_as=UNOP)
def arc_tangent(s):
    return trig_wrapper(s, math.tan)

Mode(name=TRIG_MODE_NAME, default_value='radians',
     allowable_values=('degrees', 'radians'))
ModeChange(key='d', description='degrees', menu=trig_menu, mode_name=TRIG_MODE_NAME,
           to_value='degrees')
ModeChange(key='r', description='radians', menu=trig_menu, mode_name=TRIG_MODE_NAME,
           to_value='radians')


##############
# LOGARITHMS #
##############

log_menu = Menu('l', 'log menu', parent=main_menu)

@Function('l', menu=log_menu, pop=1, push=1, description='log x',
          log_as="log {0} = {1}")
def log(s):
    return s[0].log10()

@Function('1', menu=log_menu, pop=1, push=1, description='10^x',
          log_as="10^{0} = {1}")
def tentothex(s):
    return 10 ** s[0]

@Function('n', menu=log_menu, pop=1, push=1, description='ln x',
          log_as="ln {0} = {1}")
def ln(s):
    return s[0].ln()

@Function('n', menu=log_menu, pop=1, push=1, description='e^x',
          log_as="e^{0} = {1}")
def etothex(s):
    return s[0].exp()


#############
# CONSTANTS #
#############

constants_menu = Menu(CONSTANT_MENU_CHARACTER, 'insert constant', main_menu)
Constant(math.pi, 'p', description='pi', menu=constants_menu)
Constant(math.e, 'e', description='e', menu=constants_menu)


#################
# MISCELLANEOUS #
#################

@Function('y', menu=main_menu, pop=1, push=1, description='yank bos to cboard',
          log_as="yank {0} to clipboard")
def yank_bos(s):
    """
    Use xsel to yank bottom of stack. This probably only works on Unix-like
    systems.
    """
    # help from: http://stackoverflow.com/questions/7606062/
    # is-there-a-way-to-directly-send-a-python-output-to-clipboard
    from subprocess import Popen, PIPE
    p = Popen(['xsel', '-bi'], stdin=PIPE)
    p.communicate(input=str(s[0]).encode())
    status.advisory('"%s" placed on system clipboard.' % str(s[0]))
    return s[0] # return to stack

@Function('S', menu=main_menu, pop=-1, push=1, description='sum entire stack',
          log_as=(lambda _, retval: f"sum entire stack = {retval[0]}"))
def sum_entire_stack(s):
    return sum(i.decimal for i in s)

@Function('T', menu=main_menu, pop=1, push=1, description='add MN sales tax',
          log_as=lambda args, retval: f"+7.375% tax on {args[0]} = {retval[0]}")
def add_mn_sales_tax(s):
    "Add sales tax to bos, using the rate for the Minnesota locality where I live."
    tax_rate = Decimal(.07375)
    tax = tax_rate * s[0]
    return s[0] + tax

@Function('I', menu=main_menu, pop=1, push=1, description='increment the value on the bottom', log_as=UNOP)
def increment(s):
    return s + 1
