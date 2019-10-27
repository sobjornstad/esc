from decimal import Decimal

import pytest
from esc.stack import StackItem, StackState

# pylint: disable=redefined-outer-name


@pytest.fixture
def sample_stack():
    "Return a nice, boring sample stack."
    ss = StackState()
    ss.push((StackItem(decval=Decimal("2")), ))
    ss.push((StackItem(decval=Decimal("4")), ))
    return ss


## Properties
def test_bos(sample_stack):
    "bos is the last item on the stack and can be set and deleted."
    newval = Decimal("7")
    ss = sample_stack

    assert ss.bos == ss.s[-1]

    ss.bos = StackItem(decval=newval)
    assert ss.bos == ss.s[-1]
    assert ss.bos.decimal == newval

    del ss.bos
    assert ss.bos == ss.s[-1], ss.s
    assert ss.bos.decimal == Decimal("2")


def test_bos_empty():
    "If there's nothing on the stack, bos is None."
    ss = StackState()
    assert ss.bos is None


def test_set_bos_empty():
    "If there's nothing on the stack, setting bos adds an item."
    ss = StackState()
    assert ss.is_empty
    new_item = StackItem(decval=Decimal("5"))
    ss.bos = new_item
    assert ss.bos == new_item
    assert not ss.is_empty


def test_delete_bos_empty():
    "If there's nothing on the stack, deleting bos raises an exception."
    ss = StackState()
    with pytest.raises(IndexError):
        del ss.bos


def iter_stack(sample_stack):
    "Iterating over a StackState returns the StackItems."
    lst = list(iter(sample_stack))
    assert lst[0].string == "2"
    assert lst[1].string == "4"


### Workflows
def test_add_item(sample_stack):
    """
    You add new items to the stack by using add_partial.
    """
    assert not sample_stack.editing_last_item
    assert len(sample_stack.s) == 2

    sample_stack.add_character("1")
    assert sample_stack.editing_last_item
    assert len(sample_stack.s) == 3
    assert sample_stack.bos.decimal is None

    sample_stack.add_character(".")
    sample_stack.add_character("7")
    assert sample_stack.backspace() == 0
    sample_stack.add_character("2")
    assert sample_stack.enter_number()
    assert sample_stack.bos.decimal == Decimal("1.2")

    # If we do it a second time, we get False back.
    assert not sample_stack.enter_number()


test_cases = [
    ("23", (0,), "2"),
    ("1.4", (0, 0, 1), None),
    ("2", (1, -1, -1), None),
]
@pytest.mark.parametrize("chars,backspace_results, end_state", test_cases)
def test_backspace(sample_stack, chars, backspace_results, end_state):
    "Backspace should have return values describing what happened."
    for c in chars:
        sample_stack.add_character(c)
    for retval in backspace_results:
        assert sample_stack.backspace() == retval

    if end_state is None:
        # If we backspaced everything, bos won't exist any more.
        assert len(sample_stack.s) == 2
    else:
        assert sample_stack.bos.string == end_state



def test_clear(sample_stack):
    assert len(sample_stack.s) == 2
    sample_stack.clear()
    assert len(sample_stack.s) == 0
