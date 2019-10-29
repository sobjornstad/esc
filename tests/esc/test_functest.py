from decimal import Decimal
import pytest

from esc.commands import Menu, Operation, main_menu
from esc.oops import FunctionProgrammingError

@Operation('Z', menu=main_menu, push=1, description="divide")
def divide(sos, bos):
    return sos / bos


@pytest.fixture(autouse=True)
def ensure_wrapper():
    """
    We need to clear the tests list on the divide function after every test,
    so we are running only the esc test defined in each pytest test on each
    pytest test run (confused yet?).
    """
    yield
    divide.tests.clear()


def division_test_case(**kwargs):
    "Get a new division test case. Kwargs are passed through to ensure."
    assert not divide.tests
    divide.ensure(**kwargs)
    op = main_menu.child('Z')
    assert len(op.function.tests) == 1
    tc = op.function.tests[0]
    return tc, op


def test_ensure_success_ok():
    "We can run a test that passes (doesn't raise an exception)."
    tc, op = division_test_case(before=[4, 2], after=[2])
    assert tc.before == [4, 2]
    assert tc.after == [2]
    assert tc.raises is None
    assert not tc.close
    tc.execute(op)  # should not raise


def test_ensure_success_fail():
    "We can run a test that fails because the result doesn't match the after assertion."

    tc, op = division_test_case(before=[4, 2], after=[7])
    with pytest.raises(FunctionProgrammingError) as excinfo:
        tc.execute(op)
    assert "failed a self-test" in str(excinfo.value)
    assert "as the final stack" in str(excinfo.value)


def test_ensure_raises_ok():
    "We can run a test that checks for raises and succeeds."
    tc, op = division_test_case(before=[4, 0], raises=ZeroDivisionError)
    tc.execute(op)  # should not raise


def test_ensure_raises_fail():
    "We can run a test that checks for raises and doesn't find any exception."
    tc, op = division_test_case(before=[4, 2], raises=ZeroDivisionError)
    with pytest.raises(FunctionProgrammingError) as excinfo:
        tc.execute(op)
    assert "failed a self-test" in str(excinfo.value)
    assert "was not raised" in str(excinfo.value)


def test_ensure_raises_wrong_type_fail():
    "We can run a test that checks for raises and gets the wrong exc type, thus fails."
    tc, op = division_test_case(before=[4, 0], raises=IsADirectoryError)
    with pytest.raises(FunctionProgrammingError) as excinfo:
        tc.execute(op)
    assert "failed a self-test" in str(excinfo.value)
    assert "was not listed as the exception type" in str(excinfo.value)


def test_ensure_wrong_data_type():
    tc, op = division_test_case(before=["quagmire", "blubber"], after=[(17, 81, 'hippopotamus')])
    with pytest.raises(FunctionProgrammingError) as excinfo:
        tc.execute(op)
    assert "tried to place a non-decimal value on a test stack" in str(excinfo.value)


def test_after_and_raises():
    "We cannot define a test case that uses both after and raises."
    tc, op = division_test_case(before=[1, 2], after=[4], raises=TypeError)
    with pytest.raises(FunctionProgrammingError) as excinfo:
        tc.execute(op)
    assert ("included both 'after' and 'raises' clauses"
            in str(excinfo.value))


def test_near_equality_missing():
    "Testing equality may not work quite right with floats by default..."
    tc, op = division_test_case(before=[0.1 + 0.2, 1], after=[0.3])
    with pytest.raises(FunctionProgrammingError) as excinfo:
        tc.execute(op)
    assert "0.29999999" in str(excinfo.value)


def test_near_equality_present():
    "...but it will if we set 'close' to True."
    tc, op = division_test_case(before=[0.1 + 0.2, 1], after=[0.3], close=True)
    tc.execute(op)  # should pass
