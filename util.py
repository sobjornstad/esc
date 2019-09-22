"""
util.py - miscellaneous numeric utility functions
"""

import decimal

def is_number(c):
    return ('0' <= c <= '9') or (c in ('.', '_', 'e'))

def remove_exponent(d):
    """
    Remove exponent and trailing zeros. Modified from the version in the
    decimal docs: if there are not enough digits of precision to express the
    coefficient without scientific notation, don't do anything.

    >>> remove_exponent(decimal.Decimal('5E+3'))
    decimal.Decimal('5000')
    """

    retval = d.normalize()
    if d == d.to_integral():
        try:
            retval = d.quantize(decimal.Decimal(1))
        except decimal.InvalidOperation:
            pass

    return retval
