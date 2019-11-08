from decimal import Decimal
import pytest

from esc import consts
from esc.stack import StackItem

# pylint: disable=invalid-name


test_items = [
    "0",
    "2",
    "2.05",
    "-12.87",
    "1.456281e+240"
] # yapf: disable

@pytest.mark.parametrize('val', test_items)
def test_stackitem_decimal(val):
    """
    StackItems can be created from decimal values. They'll then contain both
    string and decimal representations of that number.
    """
    si = StackItem(decval=Decimal(val))
    assert si.string == val
    assert str(si) == val  # should be the same
    assert repr(si)        # don't care about the value, just checking for errors
    assert si.decimal == Decimal(val)


test_items = [
    ("Inf", "Infinity"),
    ("1.45e100", "1.45e+100"),
    ("1.45e3", "1450")
] # yapf: disable

@pytest.mark.parametrize('input_, output', test_items)
def test_stackitem_friendlystring(input_, output):
    "The string representation is friendlificated by the StackItem in several ways."
    si = StackItem(decval=Decimal(input_))
    assert si.string == output


test_items = [
    "23",
    23,
    23.0
]
@pytest.mark.parametrize('val', test_items)
def test_stackitem_nondecimal(val):
    "We can't initialize with numbers that aren't of type Decimal."
    with pytest.raises(TypeError):
        StackItem(decval=val)


def test_stackitem_string_input():
    "Try entering a moderately complex number."
    si = StackItem(firstchar="2")
    si.add_character(".")
    si.add_character("3")
    si.add_character("7")
    si.add_character("e")
    si.add_character("2")
    assert si.finish_entry()
    assert si.string == "237"
    assert si.decimal == Decimal("237")


def test_stackitem_invalid_constructor():
    "We have to give either firstchar or decval as a constructor argument."
    with pytest.raises(AssertionError):
        StackItem()


def test_stackitem_backspace():
    "We can backspace a character we entered and add a different one."
    si = StackItem(firstchar="2")
    si.add_character("2")
    si.backspace()
    si.add_character("3")
    assert si.finish_entry()
    assert si.string == "23"


def test_stackitem_backspace_all():
    "Backspacing everything is a valid operation."
    si = StackItem(firstchar="2")
    si.backspace()
    si.add_character("5")
    assert si.finish_entry()
    assert si.string == "5"


def test_stackitem_finish_empty():
    "But if we finish an everything-backspaced entry, that's no good."
    si = StackItem(firstchar="2")
    si.backspace()
    assert not si.finish_entry()


def test_stackitem_backspace_too_far():
    "Backspacing too far simply does nothing."
    si = StackItem(firstchar="2")
    si.backspace()
    si.backspace()
    si.add_character("7")
    assert si.string == "7"


def test_stackitem_backspace_entered():
    "Clients must not backspace an entered StackItem. This raises AssertionError."
    si = StackItem(firstchar="2")
    si.finish_entry()
    with pytest.raises(AssertionError):
        si.backspace()


def test_stackitem_invalid_entry():
    """
    We can enter things composed of valid characters that aren't valid,
    but we can't finalize them.
    """
    si = StackItem(firstchar="2")
    si.add_character(".")
    si.add_character("e")
    si.add_character("e")
    si.add_character("8")
    si.add_character(".")

    assert not si.finish_entry()


def test_stackitem_invalid_character():
    """
    We can even enter things with characters that aren't valid numbers at all.
    """
    si = StackItem(firstchar='z')
    si.add_character("c")
    si.add_character("@")

    assert not si.finish_entry()


def test_stackitem_too_wide():
    """
    We can only add characters up to the STACKWIDTH.
    """
    si = StackItem(firstchar='1')
    for _ in range(consts.STACKWIDTH - 1):
        assert si.add_character('2')
    assert not si.add_character('3')
