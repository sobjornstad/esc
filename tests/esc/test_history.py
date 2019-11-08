from decimal import Decimal
import pytest

from esc.history import hs
from esc.stack import StackState, StackItem


@pytest.fixture
def an_ss():
    "History is global, so we need to clear it before each test."
    hs.clear()
    assert not hs.undo_stack
    assert not hs.redo_stack
    return StackState()


def test_undo_redo(an_ss):
    """
    We should be able to undo and redo things.
    """
    ss = an_ss

    # Calling enter_number() checkpoints and adds to the undo stack. We call
    # enter_number() when the user hits Enter or space, as well as just before
    # every operation, so this causes each distinct user action to get its own
    # pre-checkpoint.
    ss.add_character("2")
    ss.enter_number()
    ss.add_character("4")
    ss.enter_number()
    assert len(hs.undo_stack) == 2
    assert not hs.redo_stack
    assert ss.bos.string == "4"
    assert ss.bos.is_entered

    # Undoing things removes the last checkpoint from the undo stack and puts
    # it on the redo stack.
    hs.undo(ss)
    assert len(hs.undo_stack) == 1
    assert len(hs.redo_stack) == 1
    assert ss.bos.string == "4"
    assert not ss.bos.is_entered  # we didn't destroy the number, just back to editing

    # Clear the item we're now editing, then add a new one. The new stack state
    # will clear the redo stack and add the current state to the undo stack.
    ss.backspace()
    ss.add_character("5")
    ss.enter_number()
    assert len(hs.undo_stack) == 2
    assert len(hs.redo_stack) == 0
    assert ss.bos.string == "5"
    assert ss.bos.is_entered

    # Undoing and redoing works as expected.
    hs.undo(ss)
    assert len(hs.undo_stack) == 1
    assert len(hs.redo_stack) == 1
    assert ss.bos.string == "5"
    assert not ss.bos.is_entered

    hs.redo(ss)
    assert len(hs.undo_stack) == 2
    assert len(hs.redo_stack) == 0
    assert ss.bos.string == "5"
    assert ss.bos.is_entered


def test_undo_beyond_stack(an_ss):
    ss = an_ss
    ss.add_character("4")
    ss.enter_number()

    assert len(hs.undo_stack) == 1
    assert hs.undo(ss)

    assert len(hs.undo_stack) == 0
    assert not hs.undo(ss)


def test_redo_beyond_stack(an_ss):
    assert not hs.redo(an_ss)