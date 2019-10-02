"""
functions.py -- default calculator functions
"""

# pylint: disable=invalid-name

from decimal import Decimal
import math
import platform
from subprocess import Popen, PIPE

from consts import CONSTANT_MENU_CHARACTER
from menus import UNOP, BINOP, Constant, Function, Menu, Mode, ModeChange, main_menu
import modes
from oops import InsufficientItemsError
from status import status


####################
# BASIC OPERATIONS #
####################

@Function('+', menu=main_menu, push=1, log_as=BINOP)
def add(sos, bos):
    "Add sos and bos."
    return sos + bos

@Function('-', menu=main_menu, push=1, log_as=BINOP)
def subtract(sos, bos):
    "Subtract bos from sos."
    return sos - bos

@Function('*', menu=main_menu, push=1, log_as=BINOP)
def multiply(sos, bos):
    "Multiply sos and bos."
    return sos * bos

@Function('/', menu=main_menu, push=1, log_as=BINOP)
def divide(sos, bos):
    "Divide sos by bos."
    return sos / bos

@Function('^', menu=main_menu, push=1, log_as=BINOP)
def exponentiate(sos, bos):
    "Take sos to the power of bos."
    return sos ** bos

@Function('%', menu=main_menu, push=1, log_as=BINOP)
def modulus(sos, bos):
    "Take the remainder of sos divided by bos (a.k.a., sos mod bos)."
    return sos % bos

@Function('s', menu=main_menu, push=1, log_as="sqrt {0} = {1}")
def sqrt(bos):
    "Take the square root of bos."
    return math.sqrt(bos)


####################
# STACK OPERATIONS #
####################

@Function('d', menu=main_menu, push=2, description='duplicate bos',
          log_as="duplicate {0}")
def duplicate(bos):
    """
    Duplicate bos into a new stack entry. Useful if you want to hang onto the
    value for another calculation later.
    """
    return bos, bos

@Function('x', menu=main_menu, push=2, description='exchange bos, sos',
          log_as="{1} <=> {0}")
def exchange(sos, bos):
    """
    Swap bos and sos. Useful if you enter numbers in the wrong order or when
    you need to divide a more recent result by an older one.
    """
    return bos, sos

@Function('p', menu=main_menu, push=0, description='pop off bos',
          log_as="pop bos {0}")
def pop(_):
    "Remove and discard the bottom item from the stack."
    return None

@Function('r', menu=main_menu, push=-1, description='roll off tos',
          log_as="roll off tos {0}")
def roll(*stack):
    "Remove and discard the top item from the stack."
    if not stack:
        raise InsufficientItemsError(number_required=1)
    return stack[1:]

@Function('c', menu=main_menu, push=0, description='clear stack')
def clear(*stack):  #pylint: disable=useless-return
    """
    Clear all items from the stack, giving you a clean slate but maintaining
    your calculation history.
    """
    if not stack:
        raise InsufficientItemsError(number_required=1)
    return None


###################
## TRIG FUNCTIONS #
###################

TRIG_MODE_NAME = 'trig_mode'

trig_doc = """
    Calculate the values of trigonometric functions, treating inputs as
    either degrees or radians depending on the mode.
"""

def trig_mode_display():
    return f"[{modes.get(TRIG_MODE_NAME)}]"

trig_menu = Menu('t', 'trig menu', parent=main_menu, doc=trig_doc,
                 mode_display=trig_mode_display)


def trig_wrapper(bos, func, arc=False):
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
    if modes.get(TRIG_MODE_NAME) == 'degrees' and not arc:
        bos = math.radians(bos)
    ret = func(bos)
    if modes.get(TRIG_MODE_NAME) == 'degrees' and arc:
        ret = math.degrees(ret)
    return ret

@Function('s', menu=trig_menu, push=1, description='sine', log_as=UNOP)
def sine(bos):
    """
    Take the sine of bos. Affected by the mode 'degrees' or 'radians'
    shown in the trig menu.
    """
    return trig_wrapper(bos, math.sin)

@Function('c', menu=trig_menu, push=1, description='cosine', log_as=UNOP)
def cosine(bos):
    """
    Take the cosine of bos. Affected by the mode 'degrees' or 'radians'
    shown in the trig menu.
    """
    return trig_wrapper(bos, math.cos)

@Function('t', menu=trig_menu, push=1, description='tangent', log_as=UNOP)
def tangent(bos):
    """
    Take the tangent of bos. Affected by the mode 'degrees' or 'radians'
    shown in the trig menu.
    """
    return trig_wrapper(bos, math.tan)

@Function('i', menu=trig_menu, push=1, description='arc sin', log_as=UNOP)
def arc_sine(bos):
    """
    Take the arc sine (a.k.a., inverse sine) of bos. Affected by the mode
    'degrees' or 'radians' shown in the trig menu.
    """
    return trig_wrapper(bos, math.sin)

@Function('o', menu=trig_menu, push=1, description='arc cos', log_as=UNOP)
def arc_cosine(bos):
    """
    Take the arc cosine (a.k.a., inverse cosine) of bos. Affected by the mode
    'degrees' or 'radians' shown in the trig menu.
    """
    return trig_wrapper(bos, math.cos)

@Function('a', menu=trig_menu, push=1, description='arc tan', log_as=UNOP)
def arc_tangent(bos):
    """
    Take the arc cosine (a.k.a., inverse cosine) of bos. Affected by the mode
    'degrees' or 'radians' shown in the trig menu.
    """
    return trig_wrapper(bos, math.tan)

Mode(name=TRIG_MODE_NAME, default_value='radians',
     allowable_values=('degrees', 'radians'))
ModeChange(key='d', description='degrees', menu=trig_menu, mode_name=TRIG_MODE_NAME,
           to_value='degrees')
ModeChange(key='r', description='radians', menu=trig_menu, mode_name=TRIG_MODE_NAME,
           to_value='radians')


##############
# LOGARITHMS #
##############

log_doc = """Calculate the values of natural or base-10 logarithms."""
log_menu = Menu('l', 'log menu', parent=main_menu, doc=log_doc)

@Function('l', menu=log_menu, push=1, description='log x',
          log_as="log {0} = {1}")
def log(bos):
    "Take the base-10 logarithm of bos."
    return bos.log10()

@Function('1', menu=log_menu, push=1, description='10^x',
          log_as="10^{0} = {1}")
def tentothex(bos):
    "Take 10 to the power of bos."
    return 10 ** bos

@Function('n', menu=log_menu, push=1, description='ln x',
          log_as="ln {0} = {1}")
def ln(bos):
    "Take the base-e natural logarithm of bos."
    return bos.ln()

@Function('n', menu=log_menu, push=1, description='e^x',
          log_as="e^{0} = {1}")
def etothex(bos):
    "Take e to the power of bos."
    return bos.exp()


#############
# CONSTANTS #
#############

log_doc = """Insert common mathematical constants from this menu."""
constants_menu = Menu(CONSTANT_MENU_CHARACTER, 'insert constant', main_menu,
                      doc=log_doc)
Constant(math.pi, 'p', description='pi', menu=constants_menu)
Constant(math.e, 'e', description='e', menu=constants_menu)


#################
# MISCELLANEOUS #
#################

@Function('y', menu=main_menu, push=0, description='yank bos to cboard',
          retain=True, log_as="yank {0} to clipboard")
def yank_bos(bos_str):
    """
    Copy the value of bos to your system clipboard.
    """
    cmd = {
        'Windows': ['clip'],
        'Darwin': ['pbcopy'],
        'Linux': ['xsel', '-bi'],
    }[platform.system()]
    p = Popen(cmd, stdin=PIPE)
    p.communicate(input=bos_str.encode())
    status.advisory(f'"{bos_str}" placed on system clipboard.')

@Function('S', menu=main_menu, push=1, description='sum entire stack',
          log_as=(lambda retval: f"sum entire stack = {retval[0]}"))
def sum_entire_stack(*stack):
    "Sum every item on the stack into one value."
    if not stack:
        raise InsufficientItemsError(number_required=2)
    return sum(stack)

@Function('T', menu=main_menu, push=1, description='add MN sales tax',
          log_as=lambda args, retval: f"+7.375% tax on {args[0]} = {retval[0]}")
def add_mn_sales_tax(bos):
    "Add sales tax to bos, using the rate for the Minnesota locality where I live."
    tax_rate = Decimal(.07375)
    tax = tax_rate * bos
    return bos + tax

@Function('I', menu=main_menu, push=1,
          description='increment the value on the bottom', log_as=UNOP)
def increment(bos):
    "Add 1 to bos."
    return bos + 1

@Function('R', menu=main_menu, push=1, description='Sum all registers',
          log_as=lambda retval: f"sum all registers = {retval[0]}")
def sum_reg(registry):
    "Sum the values of all registers. Example function."
    values = registry.values()
    if not values:
        raise Exception("Oops, there aren't any registers")
    return sum(i.decimal for i in values)
