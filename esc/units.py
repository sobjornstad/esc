"""
units.py - symbolic unit annotations for stack items

Units are purely symbolic -- no conversion, renaming, or abbreviation handling.
The goal is to catch dimensional mistakes by checking your work.
"""

import re
from decimal import Decimal
from enum import Enum, auto


def _canonical_token(token):
    """
    Return the canonical form of a unit token by stripping a trailing 's'
    if the token is longer than one character.

    >>> _canonical_token("meters")
    'meter'
    >>> _canonical_token("m")
    'm'
    >>> _canonical_token("hours")
    'hour'
    >>> _canonical_token("s")
    's'
    """
    if len(token) > 1 and token.endswith('s'):
        return token[:-1]
    return token


def _merge_token(result, token, exp):
    """
    Add *exp* to the exponent for *token* in *result*, merging with any
    existing key whose canonical form matches.

    >>> d = {"meter": 1}
    >>> _merge_token(d, "meters", 1)
    >>> d
    {'meter': 2}
    >>> d2 = {"hours": -1}
    >>> _merge_token(d2, "hour", 1)
    >>> d2
    {'hours': 0}
    """
    canon = _canonical_token(token)
    for existing in result:
        if _canonical_token(existing) == canon:
            result[existing] = result[existing] + exp
            return
    result[token] = result.get(token, 0) + exp


def _canonical_exponents(exponents):
    """
    Return a dict with canonical token keys, merging any plural/singular
    variants. Used for comparison operations.

    >>> _canonical_exponents({"meters": 1}) == _canonical_exponents({"meter": 1})
    True
    """
    result = {}
    for token, exp in exponents.items():
        canon = _canonical_token(token)
        result[canon] = result.get(canon, 0) + exp
    # Filter out zero exponents
    return {k: v for k, v in result.items() if v != 0}


class UnitExpression:
    """
    A symbolic unit expression stored as a dict mapping token strings to
    integer exponents.

    Examples:
        >>> UnitExpression({"miles": 1}).display()
        'miles'
        >>> UnitExpression({"miles": 1, "hours": -1}).display()
        'miles / hours'
        >>> UnitExpression({"feet": 3}).display()
        'feet^3'
        >>> UnitExpression({"seconds": -1}).display()
        'seconds^-1'
        >>> UnitExpression({"m": 1, "s": -2}).display()
        'm / s^2'
    """

    def __init__(self, exponents=None):
        if exponents is None:
            self._exponents = {}
        else:
            # Filter out zero exponents
            self._exponents = {k: v for k, v in exponents.items() if v != 0}

    @property
    def exponents(self):
        return dict(self._exponents)

    @property
    def is_unitless(self):
        """
        True if this expression has no non-zero exponents.

        >>> UnitExpression({}).is_unitless
        True
        >>> UnitExpression({"m": 0}).is_unitless
        True
        >>> UnitExpression({"m": 1}).is_unitless
        False
        """
        return not self._exponents

    def __eq__(self, other):
        """
        >>> UnitExpression({"meter": 1}) == UnitExpression({"meters": 1})
        True
        >>> UnitExpression({"m": 1}) == UnitExpression({"m": 1})
        True
        """
        if isinstance(other, UnitExpression):
            return (_canonical_exponents(self._exponents)
                    == _canonical_exponents(other._exponents))
        return NotImplemented

    def __repr__(self):
        return f"UnitExpression({self._exponents!r})"

    def __hash__(self):
        return hash(tuple(sorted(_canonical_exponents(self._exponents).items())))

    def add(self, other):
        """
        Unit algebra for addition/subtraction: units must match.

        >>> m = UnitExpression({"m": 1})
        >>> m.add(UnitExpression({"m": 1})) == m
        True
        >>> UnitExpression({}).add(UnitExpression({})).is_unitless
        True
        >>> UnitExpression({"meter": 1}).add(UnitExpression({"meters": 1})).display()
        'meter'
        """
        from .oops import IncommensurableUnitsError
        if (_canonical_exponents(self._exponents)
                != _canonical_exponents(other._exponents)):
            raise IncommensurableUnitsError(self, other)
        return UnitExpression(self._exponents)

    def multiply(self, other):
        """
        Unit algebra for multiplication: add exponents.

        >>> m = UnitExpression({"m": 1})
        >>> s = UnitExpression({"s": 1})
        >>> m.multiply(s) == UnitExpression({"m": 1, "s": 1})
        True
        >>> m.multiply(UnitExpression({"m": 1})) == UnitExpression({"m": 2})
        True
        >>> m.multiply(UnitExpression({})) == m
        True
        >>> UnitExpression({"meter": 1}).multiply(UnitExpression({"meters": 1}))
        UnitExpression({'meter': 2})
        """
        result = dict(self._exponents)
        for token, exp in other._exponents.items():
            _merge_token(result, token, exp)
        return UnitExpression(result)

    def divide(self, other):
        """
        Unit algebra for division: subtract exponents.

        >>> m = UnitExpression({"m": 1})
        >>> s = UnitExpression({"s": 1})
        >>> m.divide(s) == UnitExpression({"m": 1, "s": -1})
        True
        >>> m.divide(m).is_unitless
        True
        >>> UnitExpression({"meters": 1}).divide(UnitExpression({"meter": 1})).is_unitless
        True
        """
        result = dict(self._exponents)
        for token, exp in other._exponents.items():
            _merge_token(result, token, -exp)
        return UnitExpression(result)

    def power(self, n):
        r"""
        Unit algebra for exponentiation: multiply all exponents by n.
        n must be an integer.

        >>> UnitExpression({"m": 1}).power(2) == UnitExpression({"m": 2})
        True
        >>> UnitExpression({"m": 1}).power(0).is_unitless
        True
        >>> UnitExpression({"m": 1}).power(2.5)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        esc.oops.UnitExponentError: ...
        """
        from .oops import UnitExponentError
        if not _is_integer(n):
            raise UnitExponentError(
                "Cannot raise unitful value to a non-integer power.")
        n_int = int(n)
        result = {k: v * n_int for k, v in self._exponents.items()}
        return UnitExpression(result)

    def root(self, n):
        """
        Unit algebra for roots: divide all exponents by n.
        All exponents must be evenly divisible.

        >>> UnitExpression({"m": 2}).root(2) == UnitExpression({"m": 1})
        True
        >>> UnitExpression({"m": 4, "s": -2}).root(2)
        UnitExpression({'m': 2, 's': -1})
        """
        from .oops import UnitRootError
        result = {}
        for token, exp in self._exponents.items():
            if exp % n != 0:
                raise UnitRootError(
                    f"Cannot simplify units through root: "
                    f"{token}^{exp} is not divisible by {n}.")
            result[token] = exp // n
        return UnitExpression(result)

    def display(self):
        """
        Render the unit expression for screen display.

        Positive-exponent tokens first (joined by ' * ' if multiple),
        then ' / ' and negative-exponent tokens. Exponents shown as ^n
        when |n| > 1. If ALL exponents are negative, use ^-n notation.

        >>> UnitExpression({"m": 1}).display()
        'm'
        >>> UnitExpression({"m": 2}).display()
        'm^2'
        >>> UnitExpression({"m": 1, "s": -1}).display()
        'm / s'
        >>> UnitExpression({"m": 1, "s": -2}).display()
        'm / s^2'
        >>> UnitExpression({"m": 1, "kg": 1, "s": -2}).display()
        'kg * m / s^2'
        >>> UnitExpression({"s": -1}).display()
        's^-1'
        >>> UnitExpression({"s": -2}).display()
        's^-2'
        >>> UnitExpression({}).display()
        ''
        """
        if not self._exponents:
            return ''

        pos = sorted((t, e) for t, e in self._exponents.items() if e > 0)
        neg = sorted((t, e) for t, e in self._exponents.items() if e < 0)

        def _fmt_token(token, exp):
            if abs(exp) == 1:
                return token
            return f"{token}^{abs(exp)}"

        # If ALL exponents are negative, use ^-n notation
        if not pos:
            parts = []
            for token, exp in neg:
                if exp == -1:
                    parts.append(f"{token}^-1")
                else:
                    parts.append(f"{token}^{exp}")
            return " * ".join(parts)

        pos_str = " * ".join(_fmt_token(t, e) for t, e in pos)
        if not neg:
            return pos_str

        neg_str = " * ".join(_fmt_token(t, e) for t, e in neg)
        return f"{pos_str} / {neg_str}"

    @staticmethod
    def parse(text):
        """
        Parse a unit expression from user input.

        Supports tokens separated by * and /, with optional ^N exponents.

        >>> UnitExpression.parse("miles") == UnitExpression({"miles": 1})
        True
        >>> UnitExpression.parse("miles / hours") == UnitExpression({"miles": 1, "hours": -1})
        True
        >>> UnitExpression.parse("feet^3") == UnitExpression({"feet": 3})
        True
        >>> UnitExpression.parse("m * s^-2") == UnitExpression({"m": 1, "s": -2})
        True
        >>> UnitExpression.parse("m/s") == UnitExpression({"m": 1, "s": -1})
        True
        >>> UnitExpression.parse("m^0").is_unitless
        True
        >>> UnitExpression.parse("$").display()
        '$'
        >>> UnitExpression.parse("$^2").display()
        '$^2'
        """
        text = text.strip()
        if not text:
            return UnitExpression({})

        exponents = {}
        # Split into tokens by * and /, tracking the operator
        # First normalize: ensure spaces around * and /
        parts = re.split(r'\s*([*/])\s*', text)

        sign = 1  # 1 for multiply, -1 for divide
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part == '*':
                sign = 1
                continue
            if part == '/':
                sign = -1
                continue

            # Parse token^exponent
            # Token is any non-whitespace chars except *, /, ^
            # but must not be purely digits
            match = re.match(r'^([^\s*/^]+)\^(-?\d+)$', part)
            if match:
                token = match.group(1)
                exp = int(match.group(2))
            else:
                if not re.match(r'^[^\s*/^]+$', part):
                    raise ValueError(f"Invalid unit token: '{part}'")
                token = part
                exp = 1

            if re.match(r'^\d+$', token):
                raise ValueError(f"Invalid unit token: '{token}'")

            exponents[token] = exponents.get(token, 0) + exp * sign

        return UnitExpression(exponents)


class UnitHandling(Enum):
    """
    Enum describing how an operation handles units.

    All situations described as "invalid" give the user a warning if they obtain,
    which the user can override by pressing the operation key again;
    this will carry out the operation as unitless and strip units from the result.
    """
    ADDITIVE = auto()  #: Both inputs must have same units; result uses same units.
    MULTIPLICATIVE = auto()  #: Exponents of input units are added.
    DIVISIVE = auto()  #: Exponents of input units are subtracted.
    POWER = auto(
    )  #: Exponents of input are multiplied by exponent value; exponent must be unitless or the operation is invalid.
    #: Exponents of input are divided by root degree; must yield an integer exponent or the operation is invalid.
    #: Unlike all other unit handling behaviors, the root degree must be specified
    #: as the second value in a tuple when passed to the :func:`@Operation <esc.commands.Operation>` decorator:
    #: e.g., ``(UnitHandling.ROOT, 2)`` for square root.
    ROOT = auto()
    PRESERVE = auto(
    )  #: Result keeps same units as the last input (normally used only when there is a single input).
    NO_OUTPUT = auto()  #: Operation doesn't push anything; units are irrelevant.
    NO_INPUT = auto()  #: Operation has no inputs and result is unitless.
    UNSPECIFIED = auto(
    )  #: Operation doesn't support/define unit behavior; operations on unitful quantities are invalid.


class UnitDecimal(Decimal):
    """
    Subclass of Decimal with an optional .unit attribute (UnitExpression or None).

    This avoids exposing type changes in user-facing APIs -- anything that
    received a Decimal still receives a Decimal.

    >>> ud = UnitDecimal(42, unit=UnitExpression({"m": 1}))
    >>> isinstance(ud, Decimal)
    True
    >>> ud.unit.display()
    'm'
    >>> str(ud)
    '42 m'
    >>> str(UnitDecimal(42))
    '42'
    """

    def __new__(cls, value='0', context=None, unit=None):
        instance = super().__new__(cls, value, context)
        instance.unit = unit
        return instance

    def __str__(self):
        base = super().__str__()
        if self.unit is not None and not self.unit.is_unitless:
            return f"{base} {self.unit.display()}"
        return base

    def __repr__(self):
        if self.unit is not None and not self.unit.is_unitless:
            return f"UnitDecimal('{super().__str__()}', unit={self.unit!r})"
        return f"UnitDecimal('{super().__str__()}')"


def _is_integer(n):
    """
    Check if a numeric value is an integer.

    >>> _is_integer(2)
    True
    >>> _is_integer(Decimal('2'))
    True
    >>> _is_integer(Decimal('2.5'))
    False
    >>> _is_integer(2.0)
    True
    """
    if isinstance(n, int):
        return True
    if isinstance(n, (float, Decimal)):
        return n == int(n)
    return False
