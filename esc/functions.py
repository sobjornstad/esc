"""
functions.py -- default calculator functions
"""

# pylint: disable=invalid-name

from decimal import Decimal, InvalidOperation
import math
import platform
from subprocess import Popen, PIPE

from .commands import BINOP, Constant, Operation, Menu, main_menu
from .consts import CONSTANT_MENU_CHARACTER
from .oops import InsufficientItemsError
from .status import status
from .oops import IncommensurableUnitsError
from .units import UnitDecimal as UD, UnitExpression as U, UnitHandling


####################
# BASIC OPERATIONS #
####################

@Operation('+', menu=main_menu, push=1, log_as=BINOP,
           unit_handling=UnitHandling.ADDITIVE)
def add(sos, bos):
    "Add sos and bos."
    return sos + bos

add.ensure(before=[2, 2], after=[4])
add.ensure(before=[2, -3], after=[-1])
add.ensure(before=[1, 2, 3], after=[1, 5])
# Unit tests: matching units preserved
add.ensure(
    before=[UD(2, unit=U({"m": 1})), UD(3, unit=U({"m": 1}))],
    after=[UD(5, unit=U({"m": 1}))])
# Unit tests: mismatched units raise error
add.ensure(
    before=[UD(2, unit=U({"m": 1})), UD(3, unit=U({"s": 1}))],
    raises=IncommensurableUnitsError)


@Operation('-', menu=main_menu, push=1, log_as=BINOP,
           unit_handling=UnitHandling.ADDITIVE)
def subtract(sos, bos):
    "Subtract bos from sos."
    return sos - bos

subtract.ensure(before=[3, 2], after=[1])


@Operation('*', menu=main_menu, push=1, log_as=BINOP,
           unit_handling=UnitHandling.MULTIPLICATIVE)
def multiply(sos, bos):
    "Multiply sos and bos."
    return sos * bos

multiply.ensure(before=[4, 6], after=[24])
# Unit test: multiply combines units
multiply.ensure(
    before=[UD(2, unit=U({"m": 1})), UD(4, unit=U({"s": -1}))],
    after=[UD(8, unit=U({"m": 1, "s": -1}))])
# Unit test: unitful * 1 is identity
multiply.ensure(
    before=[UD(5, unit=U({"m": 1})), UD(1)],
    after=[UD(5, unit=U({"m": 1}))])


@Operation('/', menu=main_menu, push=1, log_as=BINOP,
           unit_handling=UnitHandling.DIVISIVE)
def divide(sos, bos):
    "Divide sos by bos."
    return sos / bos

divide.ensure(before=[8, 4], after=[2])
divide.ensure(before=[8, 3], after=[Decimal(8)/3])
divide.ensure(before=[5, 0], raises=ZeroDivisionError)
# Unit test: divide subtracts exponents
divide.ensure(
    before=[UD(10, unit=U({"m": 1})), UD(2, unit=U({"s": 1}))],
    after=[UD(5, unit=U({"m": 1, "s": -1}))])
# Unit test: 1 / unitful gives reciprocal units
divide.ensure(
    before=[UD(1), UD(5, unit=U({"m": 1}))],
    after=[UD(Decimal(1)/5, unit=U({"m": -1}))])


@Operation('^', menu=main_menu, push=1, log_as=BINOP,
           unit_handling=UnitHandling.POWER)
def exponentiate(sos, bos):
    "Take sos to the power of bos."
    return sos**bos

exponentiate.ensure(before=[3, 3], after=[27])
exponentiate.ensure(before=[6, 1], after=[6])
exponentiate.ensure(before=[6, 0], after=[1])
exponentiate.ensure(before=[6, -1], after=[Decimal(1)/6])
exponentiate.ensure(before=[6, -2], after=[Decimal(1)/36])


@Operation('%', menu=main_menu, push=1, log_as=BINOP,
           unit_handling=UnitHandling.ADDITIVE)
def modulus(sos, bos):
    "Take the remainder of sos divided by bos (a.k.a., sos mod bos)."
    return sos % bos

modulus.ensure(before=[6, 2], after=[0])
modulus.ensure(before=[6, 4], after=[2])
modulus.ensure(before=[6, -4], after=[2])
modulus.ensure(before=[6, 0], raises=InvalidOperation)  # undefined


@Operation('s', menu=main_menu, push=1, log_as="sqrt {0} = {1}",
           unit_handling=(UnitHandling.ROOT, 2))
def sqrt(bos):
    "Take the square root of bos."
    return math.sqrt(bos)

sqrt.ensure(before=[25], after=[5])
sqrt.ensure(before=[0], after=[0])
sqrt.ensure(before=[-2], raises=ValueError)


####################
# STACK OPERATIONS #
####################

@Operation('d', menu=main_menu, push=2,
           description='duplicate bos',
           log_as="duplicate {0}",
           unit_handling=UnitHandling.PRESERVE)
def duplicate(bos):
    """
    Duplicate bos into a new stack entry. Useful if you want to hang onto the
    value for another calculation later.
    """
    return bos, bos

duplicate.ensure(before=[3, 2], after=[3, 2, 2])


@Operation('x', menu=main_menu, push=2,
           description='exchange bos, sos',
           log_as="{1} <=> {0}",
           unit_handling=lambda u: [u[1], u[0]])
def exchange(sos, bos):
    """
    Swap bos and sos. Useful if you enter numbers in the wrong order or when
    you need to divide a more recent result by an older one.
    """
    return bos, sos

exchange.ensure(before=[1, 2, 3], after=[1, 3, 2])


@Operation('p', menu=main_menu, push=0, description='pop off bos', log_as="pop bos {0}",
           unit_handling=UnitHandling.NO_OUTPUT)
def pop(_):
    "Remove and discard the bottom item from the stack."
    return None

pop.ensure(before=[1, 5], after=[1])
pop.ensure(before=[5], after=[])
pop.ensure(before=[], raises=InsufficientItemsError)


@Operation('r', menu=main_menu, push=-1,
           description='roll up',
           log_as="roll tos {0} to bos",
           unit_handling=lambda u: [*u[1:], u[0]])
def roll(*stack):
    "Move the top item on the stack to the bottom."
    if len(stack) < 2:
        raise InsufficientItemsError(number_required=2)
    return (*stack[1:], stack[0])

roll.ensure(before=[1, 2, 3], after=[2, 3, 1])
roll.ensure(before=[1, 2], after=[2, 1])
roll.ensure(before=[1], raises=InsufficientItemsError)
roll.ensure(before=[], raises=InsufficientItemsError)


@Operation('c', menu=main_menu, push=0, description='clear stack',
           unit_handling=UnitHandling.NO_OUTPUT)
def clear(*stack):  #pylint: disable=useless-return
    """
    Clear all items from the stack, giving you a clean slate but maintaining
    your calculation history.
    """
    if not stack:
        raise InsufficientItemsError(number_required=1)
    return None

clear.ensure(before=[6, 8, 2], after=[])
clear.ensure(before=[1], after=[])
clear.ensure(before=[], raises=InsufficientItemsError)


#############
# CONSTANTS #
#############

log_doc = """Insert common mathematical constants from this menu."""
constants_menu = Menu(CONSTANT_MENU_CHARACTER,
                      'insert constant',
                      main_menu,
                      doc=log_doc)
Constant(math.pi, 'p', description='pi', menu=constants_menu)
Constant(math.e, 'e', description='e', menu=constants_menu)


#################
# MISCELLANEOUS #
#################

@Operation('y', menu=main_menu, push=0,
           description='yank bos to cboard',
           retain=True,
           log_as="yank {0} to clipboard",
           simulate=False,
           unit_handling=UnitHandling.NO_OUTPUT)
def yank_bos(bos_str_with_units, testing):
    """
    Copy the value of bos to your system clipboard.
    """
    cmd = {
        'Windows': ['clip'],
        'Darwin': ['pbcopy'],
        'Linux': ['xsel', '-bi'], }[platform.system()]
    if not testing:
        p = Popen(cmd, stdin=PIPE)
        p.communicate(input=bos_str_with_units.encode())
    status.advisory(f'"{bos_str_with_units}" placed on system clipboard.')

yank_bos.ensure(before=[3, 5], after=[3, 5])
yank_bos.ensure(before=[], raises=InsufficientItemsError)

from .oops import UnitlessOperandError
def distance_velocity_unit_handler(units):
    if (not all(u.is_unitless for u in units)) and any(u.is_unitless for u in units):
        raise UnitlessOperandError()
    return [
        units[0].multiply(units[1]).multiply(units[1]),
        units[0].multiply(units[1]),
    ]

@Operation(key='a', menu=main_menu, push=2, 
            description='dist/vel',
            log_as="accel {0} for {1}: travels {2} and reaches {3}",
            unit_handling=distance_velocity_unit_handler)
def distance_and_final_velocity_from_standing(acceleration, time):
    return [
        time * time * acceleration / 2,
        time * acceleration,
    ]
