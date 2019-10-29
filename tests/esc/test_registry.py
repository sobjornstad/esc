from decimal import Decimal
import pytest

from esc.oops import InvalidNameError
from esc.registers import Registry
from esc.stack import StackItem

# pylint: disable=redefined-outer-name


@pytest.fixture
def sample_registry():
    reg = Registry()
    # intentionally disordered to ensure items() sorts them
    reg['b'] = StackItem(decval=Decimal(50))
    reg['a'] = StackItem(decval=Decimal(25))
    return reg


def test_retrieve(sample_registry):
    assert sample_registry['a'].string == "25"
    assert sample_registry['b'].string == "50"


def test_itervalues(sample_registry):
    needed_values = set(("25", "50"))
    actual_values = set(i.string for i in sample_registry.values())
    assert needed_values == actual_values


def test_iteritems(sample_registry):
    needed_pairs = [('a', '25'), ('b', '50')]
    actual_pairs = list((i[0], i[1].string) for i in sample_registry.items())
    assert needed_pairs == actual_pairs


test_names = ['0', 'aa', '+']
@pytest.mark.parametrize("name", test_names)
def test_setitem_invalid_name(sample_registry, name):
    with pytest.raises(InvalidNameError):
        sample_registry[name] = 24


def test_delete(sample_registry):
    assert len(sample_registry.values()) == 2
    assert 'b' in sample_registry

    del sample_registry['b']

    assert len(sample_registry.values()) == 1
    assert 'b' not in sample_registry
    assert 'a' in sample_registry
    assert sample_registry['a'].string == "25"
    with pytest.raises(KeyError):
        sample_registry['b']


def test_delete_all(sample_registry):
    assert sample_registry
    assert len(sample_registry) == 2

    del sample_registry['a']
    del sample_registry['b']

    assert not sample_registry
    assert len(sample_registry) == 0
