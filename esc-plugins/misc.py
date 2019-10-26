"""
misc.py - esc plugin demonstrating some miscellaneous useful custom esc functions
Copyright (c) 2019 Soren Bjornstad.

This plugin is provided with the esc distribution:
<https://github.com/sobjornstad/esc>
"""

from decimal import Decimal
from functools import reduce
from operator import add as add_operator

from esc.commands import Function, Menu, main_menu, UNOP
from esc.oops import FunctionExecutionError, InsufficientItemsError


@Function('S', menu=main_menu, push=1,
          description='sum entire stack',
          log_as=lambda retval: f"sum entire stack = {retval[0]}")
def sum_entire_stack(*stack):
    "Sum every item on the stack into one value."
    if len(stack) < 2:
        raise InsufficientItemsError(number_required=2)
    return sum(stack)

sum_entire_stack.ensure(before=[], raises=InsufficientItemsError)
sum_entire_stack.ensure(before=[3], raises=InsufficientItemsError)
sum_entire_stack.ensure(before=[3, 5], after=[8])
sum_entire_stack.ensure(before=list(range(10)),
                        after=[reduce(add_operator, range(10))])


@Function('T', menu=main_menu, push=1,
          description='add MN sales tax',
          log_as=lambda args, retval: f"+7.375% tax on {args[0]} = {retval[0]}")
def add_mn_sales_tax(bos):
    "Add sales tax to bos, using the rate for the Minnesota locality where I live."
    tax_rate = Decimal(".07375")
    tax = tax_rate * bos
    return bos + tax

add_mn_sales_tax.ensure(before=[0], after=[0])
add_mn_sales_tax.ensure(before=[Decimal("10.00")], after=[Decimal("10.7375")])


@Function('I', menu=main_menu, push=1,
          description='increment the value on the bottom',
          log_as=UNOP)
def increment(bos):
    "Add 1 to bos."
    return bos + 1

increment.ensure(before=[5, 6], after=[5, 7])


@Function('D', menu=main_menu, push=1,
          description='decrement bos',
          log_as=UNOP)
def decrement(bos):
    "Subtract 1 from bos."
    return bos - 1

decrement.ensure(before=[5, 6], after=[5, 5])


@Function('R', menu=main_menu, push=1,
          description='Sum all registers',
          log_as=lambda retval: f"sum all registers = {retval[0]}")
def sum_reg(registry):
    "Sum the values of all registers. Example function."
    values = registry.values()
    if not values:
        raise FunctionExecutionError("There are no registers defined.")
    return sum(i.decimal for i in values)


submenu = Menu(key='m', description='submenu test', parent=main_menu,
               doc="A menu with a submenu on it.")
subsubmenu = Menu(key='m', description='subsubmenu test', parent=submenu,
                  doc="A menu that is a submenu of a non-main menu.")

@Function('t', menu=subsubmenu, push=1,
          description='test identity function',
          log_as=UNOP)
def identity(bos):
    "Identity function."
    return bos

@Function('E', menu=main_menu, push=0, description="explode")
def set_register_E(registry):
    registry['E'] = 64

