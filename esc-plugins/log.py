"""
log.py - esc plugin for logarithmic functions
Copyright (c) 2019 Soren Bjornstad.

This plugin is provided with the esc distribution:
<https://github.com/sobjornstad/esc>
"""

from decimal import Decimal, InvalidOperation
import math

from esc.commands import Menu, Function, main_menu


log_doc = """Calculate the values of natural or base-10 logarithms."""
log_menu = Menu('l', 'log menu', parent=main_menu, doc=log_doc)


@Function('l', menu=log_menu, push=1, description='log x', log_as="log {0} = {1}")
def log(bos):
    "Take the base-10 logarithm of bos."
    return bos.log10()

log.ensure(before=[5, 1], after=[5, 0])
log.ensure(before=[10], after=[1])
log.ensure(before=[100], after=[2])
log.ensure(before=[0], after=[Decimal("-Infinity")])
log.ensure(before=[-10], raises=InvalidOperation)


@Function('1', menu=log_menu, push=1, description='10^x', log_as="10^{0} = {1}")
def tentothex(bos):
    "Take 10 to the power of bos."
    return 10**bos

tentothex.ensure(before=[1], after=[10])
tentothex.ensure(before=[2], after=[100])
tentothex.ensure(before=[0], after=[1])
tentothex.ensure(before=[-2], after=[Decimal(1)/100])


@Function('n', menu=log_menu, push=1, description='ln x', log_as="ln {0} = {1}")
def ln(bos):
    "Take the base-e natural logarithm of bos."
    return bos.ln()

ln.ensure(before=[Decimal(math.e)], after=[1], close=True)
ln.ensure(before=[Decimal(math.e).__pow__(Decimal("5"))], after=[5], close=True)
ln.ensure(before=[0], after=[Decimal("-Infinity")])
ln.ensure(before=[-2], raises=InvalidOperation)


@Function('e', menu=log_menu, push=1, description='e^x', log_as="e^{0} = {1}")
def etothex(bos):
    "Take e to the power of bos."
    return bos.exp()

etothex.ensure(before=[2], after=[Decimal(math.e).__pow__(Decimal("2"))], close=True)
etothex.ensure(before=[0], after=[1], close=True)
etothex.ensure(before=[-2], after=[1/Decimal(math.e).__pow__(Decimal("2"))], close=True)
