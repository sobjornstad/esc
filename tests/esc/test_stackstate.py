from copy import deepcopy
from decimal import Decimal
import itertools

import pytest
from esc.consts import STACKDEPTH
from esc.oops import RollbackTransaction
from esc.stack import StackItem, StackState
from esc.util import decimalize_iterable

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


def test_iter_stack(sample_stack):
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


def test_add_invalid_item(sample_stack):
    "You get an exception if you try to add an invalid number."
    sample_stack.add_character("e")
    sample_stack.add_character(".")
    with pytest.raises(ValueError) as e:
        sample_stack.enter_number()
        assert "not a valid number" in e.msg
    with pytest.raises(ValueError) as e:
        sample_stack.enter_number(running_op="my_op")
        assert 'Cannot run "my_op"' in e.msg


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


test_cases = [
    (("4",), ("2",), 1, False),
    (("2","4"), (), 2, False),
    (("4",), ("2","4"), 1, True),
    (("2","4"), ("2","4"), 2, True),
    ((), ("2","4"), 0, False),
]
@pytest.mark.parametrize("popped, left, num, retain", test_cases)
def test_pop(sample_stack, popped, left, num, retain):
    assert [i.string for i in sample_stack.pop(num, retain)] == list(popped)
    assert [i.string for i in sample_stack.s] == list(left)


def test_pop_too_many(sample_stack):
    assert sample_stack.pop(428) is None


def test_push_stackitem(sample_stack):
    """
    We can push an iterable of StackItems onto the stack with a description
    of the operation.
    """
    new_item = StackItem(decval=Decimal(25))
    assert sample_stack.push((new_item,), description="I am the walrus")
    assert sample_stack.bos == new_item
    assert sample_stack.last_operation == "I am the walrus"


def test_push_out_of_space(sample_stack):
    "We can run out of space on the stack."
    new_item = StackItem(decval=Decimal(25))
    sample_stack.clear()
    assert sample_stack.has_push_space(1)
    assert sample_stack.free_stack_spaces == STACKDEPTH

    assert sample_stack.push(list(itertools.repeat(new_item, STACKDEPTH)))

    assert not sample_stack.has_push_space(1)
    assert sample_stack.free_stack_spaces == 0
    assert not sample_stack.push((new_item,))


def test_push_decimals(sample_stack):
    "We can push decimal values directly to the stack."
    numbers = decimalize_iterable((2, 5, 8))
    assert sample_stack.push(list(numbers))
    assert len(sample_stack.s) == 5
    assert sample_stack.as_decimal()[2:] == numbers


def test_clear(sample_stack):
    assert len(sample_stack.s) == 2
    sample_stack.clear()
    assert len(sample_stack.s) == 0


test_cases = [
    (1, ["6"]),
    (2, ["4", "6"]),
    (0, []),
    (-1, ["2", "4", "6"])
]
@pytest.mark.parametrize("num, result", test_cases)
def test_last_n_items(sample_stack, num, result):
    sample_stack.push((Decimal(6),))
    assert [i.string for i in sample_stack.last_n_items(num)] == result


def test_memento_restore(sample_stack):
    orig_stack = deepcopy(sample_stack)
    assert len(sample_stack.s) == 2
    assert orig_stack == sample_stack

    memento = sample_stack.memento()
    sample_stack.clear()
    assert len(sample_stack.s) == 0
    assert orig_stack != sample_stack

    sample_stack.restore(memento)
    assert len(sample_stack.s) == 2
    assert orig_stack == sample_stack


def test_transaction_success(sample_stack):
    assert sample_stack.bos.string == "4"
    with sample_stack.transaction():
        sample_stack.push((Decimal("86"),))
        assert sample_stack.bos.string == "86"
    assert sample_stack.bos.string == "86"


def test_transaction_rolled_back(sample_stack):
    assert sample_stack.bos.string == "4"
    with sample_stack.transaction():
        sample_stack.push((Decimal("86"),))
        assert sample_stack.bos.string == "86"
        raise RollbackTransaction("I changed my mind.")
    assert sample_stack.bos.string == "4"


def test_transaction_exception(sample_stack):
    assert sample_stack.bos.string == "4"
    with pytest.raises(ValueError):
        with sample_stack.transaction():
            sample_stack.push((Decimal("86"),))
            raise ValueError("I don't like the number 86!")
    assert sample_stack.bos.string == "4"
