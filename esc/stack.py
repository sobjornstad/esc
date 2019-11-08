"""
stack.py - the stack maintains all the numbers the calculator is handling

The stack is the heart of the RPN calculator; it's what all the functions
operate on.
"""

from contextlib import contextmanager
import copy
import decimal
from decimal import Decimal

from .consts import STACKDEPTH, STACKWIDTH
from . import history
from .oops import RollbackTransaction
from .status import status


class StackItem:
    """
    An item placed on esc's stack. At its root, this is a number, but it gets
    more complicated than that!

    For one, we need a numeric value for calculations as well as a string
    value to display on the screen. The method :meth:`finish_entry` updates
    the numeric representation from the string representation.
    We could dynamically compute the string representation
    with reasonable performance,
    but see the next paragraph for why this isn't helpful.

    For another, a stack item may be *incomplete*
    (:attr:`is_entered` attribute = ``False``).
    That's because the user doesn't enter a number all at once --
    it will typically consist of multiple keystrokes.
    If so, there won't be a decimal representation
    until we call :meth:`finish_entry`.
    The StackState is in charge of calling this method if needed
    before trying to do any calculations with the number.
    """
    def __init__(self, firstchar=None, decval=None):
        """
        We can create an item on the stack either by the user entering it (in
        which case we have methods for gradually building up a string repr of
        the value and then converting it to the Decimal value that is used for
        calculations) or by directly entering a Decimal value (for instance, as
        the result of a calculation).

        Use one of the two parameters:

        :param firstchar:
            If specified, initialize the string representation to this string
            and prepare for more characters to be entered with :meth:`add_character`.
        :param decval:
            If specified, make this Decimal the value of the StackItem
            and create a string representation from it.
        """
        #: Whether the number has been fully entered. If not entered,
        #: many methods will not work as we don't have a Decimal representation yet.
        self.is_entered = None
        #: Decimal representation.
        #: This is ``None`` if :attr:`is_entered` is ``False``.
        self.decimal = None
        #: String representation.
        self.string = None

        if firstchar is not None:
            self._init_partial(firstchar)
        elif decval is not None:
            self._init_full(decval)
        else:
            raise AssertionError("No valid argument to constructor of StackItem!")

    def __repr__(self):
        return f"<StackItem: Decimal({self.decimal}) String({self.string})>"

    def __str__(self):
        return self.string

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    @staticmethod
    def _remove_exponent(d):
        """
        Remove exponent and trailing zeros. Modified from the version in the
        decimal docs: if there are not enough digits of precision to express the
        coefficient without scientific notation, don't do anything.

        >>> StackItem._remove_exponent(decimal.Decimal('5E+3'))
        Decimal('5000')
        """

        retval = d.normalize()
        if d == d.to_integral():
            try:
                retval = d.quantize(decimal.Decimal(1))
            except decimal.InvalidOperation:
                pass

        return retval

    def _init_partial(self, firstchar):
        "Initialize a partial item from a string being entered by the user."
        self.is_entered = False
        self.decimal = None
        self.string = firstchar

    def _init_full(self, decval):
        "Initialize an item from a Decimal."
        if not isinstance(decval, Decimal):
            raise TypeError("Only Decimals are valid initial values "
                            "for the decval constructor parameter.")
        self.is_entered = True
        self.decimal = decval
        self._string_repr_from_value()

    def _string_repr_from_value(self):
        "(Re)set the string representation based on the attribute /value/."
        self.string = \
            str(self._remove_exponent(self.decimal.normalize())).replace('E', 'e')

    def add_character(self, nextchar):
        """
        Add a character to the running string
        of the number being entered on the stack.
        Calling :meth:`add_character` is illegal
        and will raise an ``AssertionError``
        if the number has already been entered completely.

        :return: ``True`` if successful,
                 ``False`` if the stack width (``esc.consts.STACKWIDTH``)
                 has been exceeded.
        """
        assert not self.is_entered, "Number already entered!"
        if len(self.string) < STACKWIDTH:
            self.string += nextchar
            return True
        else:
            return False

    def backspace(self, num_chars=1):
        """
        Remove the last character(s) from the string being entered.
        Calling :meth:`backspace` is illegal
        and will raise an ``AssertionError``
        if the number has already been entered completely.
        """
        assert not self.is_entered, "Cannot backspace an already-entered string!"
        self.string = self.string[0:-1*num_chars]

    def finish_entry(self):
        """
        Signal that the user is done entering a string
        and it should be converted to a Decimal value.
        If successful, return ``True``;
        if the entered string does not form a valid number, return ``False``.
        This should be called only by the
        ``enter_number`` method of ``StackState``.
        """
        try:
            self.decimal = Decimal(self.string)
        except decimal.InvalidOperation:
            return False
        else:
            self._string_repr_from_value()
            self.is_entered = True
            return True


class StackState:
    """
    An object containing the current state of the stack: a stack pointer, the
    screen cursor's position across on the current value, the stack itself as a
    list, and whether we are currently editing a number.

    Values may be manipulated directly as convenient. There are also several
    helper methods for convenience.

    Generally, a StackState should be initialized at the beginning of execution
    and used until the program exits. Checkpointing and undoing operate by
    exporting and restoring mementos consisting of this object's __dict__.
    """
    def __init__(self):
        self.s = []
        self.operation_history = []
        self.stack_posn = -1
        self._editing_last_item = False

    def __repr__(self):
        vals = [repr(item) if idx != self.stack_posn else f"({item!r})"
                for idx, item in enumerate(self.s)]
        if self.editing_last_item:
            vals[-1] += "..."
        return f"<StackState: {', '.join(vals)}>"

    def __iter__(self):
        for i in self.s:
            yield i

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    @property
    def editing_last_item(self):
        return self._editing_last_item

    @editing_last_item.setter
    def editing_last_item(self, value):
        self._editing_last_item = value
        #TODO: This really shouldn't be here but we can't put the status logic
        # in display either or we have a circular dependency
        if self._editing_last_item:
            status.entering_number()
        else:
            status.ready()

    @property
    def bos(self):
        "Bottom of Stack -- the last item, or None if the stack is empty."
        try:
            return self.s[self.stack_posn]
        except IndexError:
            return None

    @bos.setter
    def bos(self, value):
        try:
            self.s[self.stack_posn] = value
        except IndexError:
            self.s.append(value)

    @bos.deleter
    def bos(self):
        self.s.pop()  # raises IndexError if nothing here
        self.editing_last_item = False
        self.stack_posn -= 1

    @property
    def cursor_posn(self):
        if self.bos is None or not self.editing_last_item:
            return 0
        else:
            return len(self.bos.string)

    @property
    def free_stack_spaces(self):
        return STACKDEPTH - self.stack_posn - 1

    @property
    def is_empty(self):
        return not bool(self.s)

    @property
    def last_operation(self):
        return self.operation_history[-1] if self.operation_history else None

    def _new_entry_stack_item(self, c):
        """
        Create a new stack item for the user to type into beginning with the
        character /c/.
        """
        if not self.has_push_space(1):
            return False

        self.stack_posn += 1
        self.s.append(StackItem(firstchar=c))
        self.editing_last_item = True
        return True

    def as_decimal(self):
        """
        Return the stack as a list of its Decimal values.
        """
        return [i.decimal for i in self.s]

    def add_character(self, c):
        """
        Append to an existing incomplete item on the stack with the given
        character (or string) /c/. If bos is not incomplete, start a new
        stack item beginning with the character /c/.

        Return True if successful, False if we have exceeded the maximum
        capacity of the stack.
        """
        if self.editing_last_item:
            return self.s[self.stack_posn].add_character(c)
        else:
            return self._new_entry_stack_item(c)

    def backspace(self):
        """
        Backspace one character in the current item on the stack. Return 0 if a
        character was backspaced, 1 if the whole item was wiped out, and -1 if
        a stack item was not being edited at all.
        """
        if not self.editing_last_item:
            return -1

        assert self.bos is not None, "Editing last item without an item on the stack"
        if self.cursor_posn == 1:
            # remove the stack item in progress
            del self.bos
            return 1
        else:
            self.bos.backspace()
            return 0

    def clear(self):
        "Clear the stack."
        self.s.clear()
        self.stack_posn = -1
        self.editing_last_item = False

    def enter_number(self, running_op=None):
        """
        Finish the entry of a number.

        Return:
            True if a number was finished.
            False if bos was already finished.

        Raises:
            ValueError if the value was invalid and the number couldn't be
            finished. The exception message can be displayed on the status bar.

        Set running_op to an operation name if you're entering prior to running
        an operation (go figure) for a more helpful error message in that case.
        """
        # Even if we were *not* editing the stack, checkpoint the stack state.
        # This ensures that we will get a checkpoint anytime we call an
        # operation as well as when we enter a number onto the stack.
        # Multiple checkpoints in a row do nothing, so this is safe.
        history.hs.checkpoint_stack(self)

        if self.editing_last_item:
            if self.s[self.stack_posn].finish_entry():
                self.editing_last_item = False
                return True
            else:
                if running_op:
                    msg = 'Cannot run "%s": invalid value on bos.' % running_op
                else:
                    msg = 'Bottom of stack is not a valid number.'
                raise ValueError(msg)
        else:
            return False

    def has_push_space(self, spaces):
        return STACKDEPTH >= len(self.s) + spaces

    def push(self, vals, description=None):
        """
        Push an iterable of decimals or StackItems onto the stack.

        If a /description/ of the operation is specified, it will be recorded
        for display as a step in the history pane.
        """
        if not self.has_push_space(len(vals)):
            return False

        if description is not None:
            self.record_operation(description)

        for i in vals:
            if isinstance(i, StackItem):
                self.s.append(i)
            else:
                self.s.append(StackItem(decval=i))
        self.stack_posn += len(vals)
        return True

    def pop(self, num=1, retain=False):
        """
        Pop /num/ StackItems off the end of the stack and return them as a
        list. If there are too few items on the stack, return None.

        If /retain/ is true, don't remove the items from the stack.
        """
        if not retain:
            self.stack_posn -= num

        if len(self.s) < num:
            return None
        elif num == 0:
            # Needs a special case, as s[:-0] will wipe out the stack
            return []
        else:
            stack_slice = self.s[-num:]
            if not retain:
                self.s = self.s[:-num]
            return stack_slice

    def last_n_items(self, n):
        """
        Return the last /n/ items from the stack, with special meaning for 0
        and -1.

        n > 0   => the last n items on the stack
        n == 0  => the empty list
        n == -1 => (a shallow copy of) the entire stack

        This matches the meaning of the pop and push values used in the
        operation execution logic. An operation requests push=n>0 when it wants
        to push n items, 0 if it pushes nothing, or -1 if whatever it pushes
        should replace the entire stack.
        """
        if n == -1:
            return self.s[:]
        elif n == 0:
            return []
        else:
            return self.s[-n:]

    def record_operation(self, description):
        """
        Record that an operation happened to the stack.

        Typically this will be accomplished from the client by providing the
        description as an argument to push() when pushing back results, but
        the client may also wish to record an operation that doesn't push
        anything (for instance, when clearing the stack, or mutating the
        entire stack with a push=-1).
        """
        self.operation_history.append(description)

    def memento(self):
        """
        Generate a memento object for the current state of the stack. The
        stack can later be restored to this state by calling restore() on
        the memento.
        """
        return copy.deepcopy(self.__dict__)

    def restore(self, memento):
        """
        Restore the current object to a prior state checkpointed by calling
        memento().
        """
        self.__dict__.clear()
        self.__dict__.update(memento)
        self.editing_last_item = self._editing_last_item  # force property logic to run

    @contextmanager
    def transaction(self):
        """
        Context manager to start a stack transaction. If an exception occurs
        during the run, any changes made to the StackState will be rolled back
        before re-raising the exception. Otherwise, changes will persist.

        Raising the special exception RollbackTransaction causes the
        transaction to be rolled back but no exception to be raised. In
        addition, the message provided on RollbackTransaction will be set as
        a status-bar error. It's difficult for the caller to do this
        themselves because the act of rolling back will set the status to
        "ready" or "insert".
        """
        checkpoint = self.memento()
        try:
            yield
        except RollbackTransaction as e:
            self.restore(checkpoint)
            if e.status_message:
                status.error(e.status_message)
        except Exception:
            self.restore(checkpoint)
            raise
