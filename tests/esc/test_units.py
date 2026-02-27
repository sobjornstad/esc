"""
test_units.py - tests for the units module
"""

import pytest
from decimal import Decimal

from esc.units import (UnitExpression, UnitHandler, UnitDecimal,
                       additive_unit_handling, multiplicative_unit_handling,
                       divisive_unit_handling, power_unit_handling,
                       root_unit_handling, preserve_unit_handling,
                       no_output_unit_handling, no_input_unit_handling,
                       unspecified_unit_handling)
from esc.oops import (IncommensurableUnitsError, UnitRootError,
                      UnitExponentError)


# === UnitExpression basics ===

class TestUnitExpressionBasics:
    def test_empty_is_unitless(self):
        assert UnitExpression({}).is_unitless

    def test_zero_exponent_is_unitless(self):
        assert UnitExpression({"m": 0}).is_unitless

    def test_nonzero_is_not_unitless(self):
        assert not UnitExpression({"m": 1}).is_unitless

    def test_equality(self):
        assert UnitExpression({"m": 1}) == UnitExpression({"m": 1})

    def test_inequality(self):
        assert UnitExpression({"m": 1}) != UnitExpression({"s": 1})

    def test_exponents_property_returns_copy(self):
        u = UnitExpression({"m": 1})
        e = u.exponents
        e["m"] = 99
        assert u.exponents == {"m": 1}

    def test_repr(self):
        u = UnitExpression({"m": 1})
        assert "m" in repr(u)

    def test_hash_equal(self):
        a = UnitExpression({"m": 1, "s": -1})
        b = UnitExpression({"m": 1, "s": -1})
        assert hash(a) == hash(b)


# === UnitExpression algebra ===

class TestUnitExpressionAlgebra:
    def test_add_matching(self):
        m = UnitExpression({"m": 1})
        result = m.add(UnitExpression({"m": 1}))
        assert result == m

    def test_add_mismatched_raises(self):
        with pytest.raises(IncommensurableUnitsError):
            UnitExpression({"m": 1}).add(UnitExpression({"s": 1}))

    def test_add_unitless(self):
        result = UnitExpression({}).add(UnitExpression({}))
        assert result.is_unitless

    def test_add_unitless_vs_unitful_raises(self):
        with pytest.raises(IncommensurableUnitsError):
            UnitExpression({}).add(UnitExpression({"m": 1}))

    def test_multiply(self):
        result = UnitExpression({"m": 1}).multiply(UnitExpression({"s": 1}))
        assert result == UnitExpression({"m": 1, "s": 1})

    def test_multiply_same_unit(self):
        result = UnitExpression({"m": 1}).multiply(UnitExpression({"m": 1}))
        assert result == UnitExpression({"m": 2})

    def test_multiply_neutral(self):
        m = UnitExpression({"m": 1})
        result = m.multiply(UnitExpression({}))
        assert result == m

    def test_divide(self):
        result = UnitExpression({"m": 1}).divide(UnitExpression({"s": 1}))
        assert result == UnitExpression({"m": 1, "s": -1})

    def test_divide_cancels(self):
        result = UnitExpression({"m": 1}).divide(UnitExpression({"m": 1}))
        assert result.is_unitless

    def test_power_integer(self):
        result = UnitExpression({"m": 1}).power(3)
        assert result == UnitExpression({"m": 3})

    def test_power_zero(self):
        result = UnitExpression({"m": 2}).power(0)
        assert result.is_unitless

    def test_power_decimal_integer(self):
        result = UnitExpression({"m": 1}).power(Decimal("2"))
        assert result == UnitExpression({"m": 2})

    def test_power_non_integer_raises(self):
        with pytest.raises(UnitExponentError):
            UnitExpression({"m": 1}).power(Decimal("2.5"))

    def test_root_even(self):
        result = UnitExpression({"m": 2}).root(2)
        assert result == UnitExpression({"m": 1})

    def test_root_uneven_raises(self):
        with pytest.raises(UnitRootError):
            UnitExpression({"m": 3}).root(2)

    def test_root_multiple_tokens(self):
        result = UnitExpression({"m": 4, "s": -2}).root(2)
        assert result == UnitExpression({"m": 2, "s": -1})


# === UnitExpression display ===

class TestUnitExpressionDisplay:
    def test_empty(self):
        assert UnitExpression({}).display() == ''

    def test_single_positive(self):
        assert UnitExpression({"m": 1}).display() == 'm'

    def test_positive_exponent(self):
        assert UnitExpression({"m": 2}).display() == 'm^2'

    def test_positive_and_negative(self):
        assert UnitExpression({"m": 1, "s": -1}).display() == 'm / s'

    def test_positive_and_negative_exponent(self):
        assert UnitExpression({"m": 1, "s": -2}).display() == 'm / s^2'

    def test_all_negative(self):
        assert UnitExpression({"s": -1}).display() == 's^-1'

    def test_all_negative_higher(self):
        assert UnitExpression({"s": -2}).display() == 's^-2'

    def test_multiple_positive(self):
        d = UnitExpression({"kg": 1, "m": 1, "s": -2}).display()
        assert "kg" in d
        assert "m" in d
        assert "s^2" in d

    def test_multiple_negative(self):
        d = UnitExpression({"s": -1, "m": -1}).display()
        assert "s^-1" in d
        assert "m^-1" in d


# === UnitExpression parsing ===

class TestUnitExpressionParse:
    def test_single_token(self):
        assert UnitExpression.parse("miles") == UnitExpression({"miles": 1})

    def test_division(self):
        assert (UnitExpression.parse("miles / hours")
                == UnitExpression({"miles": 1, "hours": -1}))

    def test_exponent(self):
        assert UnitExpression.parse("feet^3") == UnitExpression({"feet": 3})

    def test_negative_exponent(self):
        assert (UnitExpression.parse("m * s^-2")
                == UnitExpression({"m": 1, "s": -2}))

    def test_no_spaces(self):
        assert (UnitExpression.parse("m/s")
                == UnitExpression({"m": 1, "s": -1}))

    def test_zero_exponent_removes(self):
        assert UnitExpression.parse("m^0").is_unitless

    def test_empty_string(self):
        assert UnitExpression.parse("").is_unitless

    def test_whitespace(self):
        assert UnitExpression.parse("  ").is_unitless

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError):
            UnitExpression.parse("123")

    def test_complex_expression(self):
        result = UnitExpression.parse("kg * m^2 / s^2")
        assert result == UnitExpression({"kg": 1, "m": 2, "s": -2})


# === UnitDecimal ===

class TestUnitDecimal:
    def test_isinstance_decimal(self):
        assert isinstance(UnitDecimal(42), Decimal)

    def test_unit_attribute(self):
        u = UnitExpression({"m": 1})
        ud = UnitDecimal(42, unit=u)
        assert ud.unit is u

    def test_str_with_unit(self):
        ud = UnitDecimal(42, unit=UnitExpression({"m": 1}))
        assert str(ud) == "42 m"

    def test_str_without_unit(self):
        assert str(UnitDecimal(42)) == "42"

    def test_str_unitless_expression(self):
        ud = UnitDecimal(42, unit=UnitExpression({}))
        assert str(ud) == "42"

    def test_arithmetic_returns_plain_decimal(self):
        ud = UnitDecimal(42, unit=UnitExpression({"m": 1}))
        result = ud + Decimal(1)
        assert isinstance(result, Decimal)
        # After arithmetic, unit is lost (expected -- Decimal operations
        # return plain Decimals)

    def test_repr_with_unit(self):
        ud = UnitDecimal(42, unit=UnitExpression({"m": 1}))
        assert "UnitDecimal" in repr(ud)
        assert "m" in repr(ud)

    def test_repr_without_unit(self):
        ud = UnitDecimal(42)
        assert "UnitDecimal" in repr(ud)


# === UnitHandler classes ===

class TestUnitHandling:
    ALL_HANDLER_CLASSES = [
        additive_unit_handling,
        multiplicative_unit_handling,
        divisive_unit_handling,
        power_unit_handling,
        preserve_unit_handling,
        no_output_unit_handling,
        no_input_unit_handling,
        unspecified_unit_handling,
    ]

    def test_all_handler_instances_are_callable(self):
        for cls in self.ALL_HANDLER_CLASSES:
            assert callable(cls())

    def test_all_handler_instances_are_unit_handler(self):
        for cls in self.ALL_HANDLER_CLASSES:
            assert isinstance(cls(), UnitHandler)

    def test_all_handlers_have_description(self):
        for cls in self.ALL_HANDLER_CLASSES:
            # root_unit_handling sets description in __init__
            if cls is root_unit_handling:
                assert root_unit_handling(2).description
            else:
                assert cls.description, f"{cls!r} has no description"

    def test_root_unit_handling(self):
        handler = root_unit_handling(2)
        assert isinstance(handler, UnitHandler)
        assert callable(handler)
        assert "2" in handler.description

    def test_root_unit_handling_different_degrees(self):
        h3 = root_unit_handling(3)
        assert "3" in h3.description
