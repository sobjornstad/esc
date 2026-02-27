"""
units.py - symbolic unit annotations for stack items

Units are purely symbolic -- no conversion, renaming, or abbreviation handling.
The goal is to catch dimensional mistakes by checking your work.
"""

import re
from decimal import Decimal

from .oops import (
    IncommensurableUnitsError,
    OperationWillRemoveUnitsError,
    ProgrammingError,
    UnitExponentError,
    UnitlessOperandError,
    UnitRootError,
)


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
            return (_canonical_exponents(self._exponents) == _canonical_exponents(
                other._exponents))
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

        Raises :class:`~esc.oops.IncommensurableUnitsError`
        if the inputs have different unit tags.
        """
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
        result = {}
        for token, exp in self._exponents.items():
            if exp % n != 0:
                raise UnitRootError(f"Cannot simplify units through root: "
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


# TODO: Probably we should supply this to users writing their own?
class UnitHandler:
    """
    A UnitHandler is a callable with the following parameters,
    bound by name to the following available kwargs:

    :param input_units: 
        A list of :class:`UnitExpression <esc.units.UnitExpression>` instances, 
        one per input in sequence.
    :param input_stackitems:
        Like ``input_units``, but gives the
        :class:`StackItem <esc.stack.StackItem>` for each input.
    :param num_results: 
        The number of results that the operation returns with these inputs.
    :param override:
        Whether the user has repeated the operation to override a unit error.

        .. note::
            **You probably do not need or want this parameter.**

            The default behavior for overrides
            is to offer the user an override, and if accepted,
            carry out the calculation unitless and push unitless results to the stack.
            You don't need to consume or use this parameter to get that behavior.

            If for your operation there is some sensible way to recover
            from a unit error/warning and still return unitful values,
            you can consume this parameter and return the units
            that should be used for the result(s) in this case.
            If some unit errors that can occur are recoverable and others are not,
            raise an exception again for the unrecoverable ones.

            This is used internally for the warning about multiplying a unitful by a
            unitless value.

    :returns:
        A list of :class:`UnitExpression <esc.units.UnitExpression>` instances,
        one for each output.

    A unit handler need only declare the parameters it actually uses.
    Most custom handlers only need ``input_units``.

    If the callable has a :attr:`description` attribute,
    or if that is not present a :attr:`__doc__` attribute (docstring),
    it will be shown in the help screen after ``Units: ``.
    In a couple of words, this should describe what happens to the units.
    """
    description = ""

    def __repr__(self):
        return f"<UnitHandler: {self.__class__.__name__}>"

    def __call__(self, input_units, input_stackitems, num_results, override):
        raise NotImplementedError("")


# pylint: disable=invalid-name


class additive_unit_handling(UnitHandler):
    """
    All inputs must have an identical unit tag (after coercion of singular/plural
    variants); the result uses that unit tag.
    A unitless input is considered to be different from all unitful inputs.
    Any number of operands are allowed.

    Raises:
        :class:`~esc.oops.IncommensurableUnitsError` if any unit tag differs.
    """
    description = "additive (units must match)"

    def __call__(self, input_units):
        base = input_units[0]
        for u in input_units[1:]:
            base = base.add(u)
        return [base]


class multiplicative_unit_handling(UnitHandler):
    """
    Unit exponents are added.
    Any number of operands are allowed.
    When some operands are unitful and others are unitless,
    a warning will be issued on the first run.

    Raises:
        :class:`~esc.oops.UnitlessOperandError` if a unitless operand is not the
        identity value (1). Unlike most unit errors, this is a warning only,
        and overriding it will carry out the calculation and process the units
        as normal (the unitless operand will not change the units of the result).
    """
    description = "multiplicative (units combine)"

    def __call__(self, input_units, input_stackitems, override):
        if any(u.is_unitless for u in input_units):
            unitless_args = [
                a for a, u in zip(input_stackitems, input_units) if u.is_unitless
            ]
            if not all(a.decimal == 1 for a in unitless_args):
                if not override:
                    raise UnitlessOperandError()
        result = input_units[0].multiply(input_units[1])
        return [result]


class divisive_unit_handling(UnitHandler):
    """
    Unit exponents are subtracted.
    Any number of operands are allowed.
    When some operands are unitful and others are unitless,
    a warning will be issued on the first run.
    
    Raises:
        :class:`~esc.oops.UnitlessOperandError` if a unitless operand is not the
        identity value (1). Unlike most unit errors, this is a warning only,
        and overriding it will carry out the calculation and process the units
        as normal (the unitless operand will not change the units of the result).
    """
    description = "divisive (units divide)"

    def __call__(self, input_units, input_stackitems, override):
        if any(u.is_unitless for u in input_units):
            unitless_args = [
                a for a, u in zip(input_stackitems, input_units) if u.is_unitless
            ]
            if not all(a.decimal == 1 for a in unitless_args):
                if not override:
                    raise UnitlessOperandError()
        result = input_units[0].divide(input_units[1])
        return [result]


class power_unit_handling(UnitHandler):
    """
    Exponents of the first input's unit are multiplied by the exponent value.
    The exponent must be unitless and integer-valued.
    Only two operands are allowed, the base and the exponent.

    Raises:
        :class:`~esc.oops.UnitExponentError` if the exponent has a unit or is
        not an integer.
        :class:`~esc.oops.ProgrammingError` (at runtime) if
        the handler is called with != 2 inputs.
    """
    description = "power (base units scaled by exponent)"

    def __call__(self, input_units, input_stackitems):
        if len(input_units) != 2:
            raise ProgrammingError(f"Invalid unit handler: "
                                   f"power handler requires exactly 2 inputs, "
                                   f"got {input_units!r}.")

        base_unit = input_units[0]
        exp_unit = input_units[1]
        if not exp_unit.is_unitless:
            raise UnitExponentError("Exponent cannot have units. "
                                    "Press again to override.")
        exp_val = input_stackitems[1].decimal
        if base_unit.is_unitless:
            return [None]
        try:
            result = base_unit.power(exp_val)
        except UnitExponentError as exc:
            raise UnitExponentError("Cannot raise unitful value to a non-integer "
                                    "power. Press again to override.") from exc
        return [result]


class root_unit_handling(UnitHandler):
    """
    Exponents of the first unit are divided by the *degree*
    specified at handler instantiation time.
    All exponents must be evenly divisible.
    Only one operand is allowed, the base.

    Raises:
        :class:`~esc.oops.UnitRootError` if any exponent is not evenly
        divisible by the degree. :class:`~esc.oops.ProgrammingError` (at
        runtime) if the handler is called with != 1 input.
    """
    def __init__(self, degree):
        if not _is_integer(degree):
            raise ProgrammingError(f"Invalid unit handler: "
                                   f"degree must be an integer (not {degree!r}).")
        self._degree = degree
        self.description = f"root (unit exponents / {degree})"

    def __call__(self, input_units):
        if len(input_units) != 1:
            raise ProgrammingError(f"Invalid unit handler: "
                                   f"root handler requires exactly 1 input, "
                                   f"got {input_units!r}.")

        base_unit = input_units[0]
        if base_unit.is_unitless:
            return [None]
        result = base_unit.root(self._degree)
        return [result]


class preserve_unit_handling(UnitHandler):
    """
    Maintain the same units as the only input.

    Raises:
        :class:`~esc.oops.ProgrammingError` (at runtime) if the handler is
        called with != 1 input.
    """
    description = "preserves units"

    def __call__(self, input_units, num_results):
        if len(input_units) != 1:
            raise ProgrammingError(f"Invalid unit handler: "
                                   f"preserve handler requires exactly 1 input, "
                                   f"got {input_units!r}.")

        base = input_units[0]
        base_or_none = base if not base.is_unitless else None
        return [base_or_none] * max(num_results, 0)


class no_output_unit_handling(UnitHandler):
    """
    The operation doesn't push anything; units are irrelevant.
    """
    description = "no output units"

    def __call__(self, num_results):
        return [None] * max(num_results, 0)


class no_input_unit_handling(UnitHandler):
    """
    The operation has no inputs and the result is unitless (e.g., unitless constants).
    """
    description = "no input units"

    def __call__(self, num_results):
        return [None] * max(num_results, 0)


class unspecified_unit_handling(UnitHandler):
    """
    The operation doesn't support unit behavior.

    Operations on unitful quantities cannot be carried out,
    but the user can choose to strip units and complete the calculation.
    """
    description = "unspecified (will strip units)"

    def __call__(self):
        raise OperationWillRemoveUnitsError()

# pylint: enable=invalid-name


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
