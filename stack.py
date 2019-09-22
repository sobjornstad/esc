import decimal
from decimal import Decimal
import copy

from display import screen
import history
import util
from consts import STACKDEPTH, STACKWIDTH


class StackItem:
    """
    An item placed on esc's stack. At its root, this is a number, but it gets
    more complicated than that!

    For one, we need a numeric value for calculations as well as a string
    value to display on the screen. The functions finish_entry() and
    _string_repr_from_value() can be used to update the numeric and string
    representations from the other. We could dynamically compute the string
    representation with reasonable performance, but see the next paragraph
    for why this isn't helpful.

    For another, a stack item may be *incomplete* (self.is_entered = False).
    That's because the user doesn't enter a number all at once, it will often
    consist of multiple keystrokes. If so, there won't be a decimal
    representation until we call finish_entry(). The StackState is in charge
    of calling this method if needed before trying to do any calculations
    with the number.
    """
    def __init__(self, firstchar=None, decval=None):
        """
        We can create an item on the stack either by the user entering it (in
        which case we have methods for gradually building up a string repr of
        the value and then converting it to the Decimal value that is used for
        calculations) or by directly entering a Decimal value (for instance, as
        the result of a calculation).
        """
        self.is_entered = None
        self.decimal = None
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

    def _init_partial(self, firstchar):
        "Initialize a partial item from a string being entered by the user."
        self.is_entered = False
        self.decimal = None
        self.string = firstchar

    def _init_full(self, decval):
        "Initialize an item from a Decimal."
        self.is_entered = True
        self.decimal = decval
        self._string_repr_from_value()

    def _string_repr_from_value(self):
        "(Re)set the string representation based on the attribute /value/."
        self.string = \
            str(util.remove_exponent(self.decimal.normalize())).replace('E', 'e')

        # If we weren't using scientific notation but the new value is too
        # long to fit in the stack window, convert it, knocking down the
        # displayed precision to fit.
        if len(self.string) > STACKWIDTH:
            precision = STACKWIDTH
            precision -= 3            # account for length of exponent
            precision -= len("0.e+")  # account for new characters
            precision -= (1 if self.decimal.as_tuple().sign == 1 else 0)
            self.string = ("%." + str(precision) + "e") % (self.decimal)

    def add_character(self, nextchar):
        """
        Add a character to the running string of the number being entered on
        the stack. Return True if successful, False if the stack width has
        been exceeded.
        """
        assert not self.is_entered, "Number already entered!"
        if len(self.string) < STACKWIDTH:
            self.string += nextchar
            return True
        else:
            return False

    def backspace(self, num_chars=1):
        """
        Remove the last character from the string being entered. Calling
        backspace() is illegal if the number has already been entered completely
        (backspacing a number is a nonsensical operation).
        """
        assert not self.is_entered, "Cannot backspace an already-entered string!"
        self.string = self.string[0:-1*num_chars]

    def finish_entry(self):
        """
        Signal that the user is done entering a string and it should be
        converted to a Decimal value. If successful, return True; if the
        entered string does not form a valid number, return False. This
        should be called from ss.enter_number() and probably nowhere else.
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
        self.stack_posn = -1
        self.cursor_posn = 0
        self.editing_last_item = False

    def __repr__(self):
        vals = [item if idx != self.stack_posn else f"({item})"
                for idx, item in enumerate(self.s)]
        if self.editing_last_item:
            vals[-1] += "..."
        return f"<StackState: {', '.join(vals)}>"

    def __iter__(self):
        for i in self.s:
            yield i

    @property
    def bos(self):
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
        self.editing_last_item = False
        self.s.pop()
        self.stack_posn -= 1
        self.cursor_posn = 0

    @property
    def free_stack_spaces(self):
        return STACKDEPTH - self.stack_posn - 1

    def add_partial(self, c):
        """
        Start a new item on the stack with the given character /c/. Return
        False if we have exceeded the maximum capacity of the stack.
        """
        if not self.has_push_space(1):
            return False

        self.stack_posn += 1
        self.cursor_posn = 0
        self.s.append(StackItem(firstchar=c))
        self.editing_last_item = True
        return True

    def backspace(self):
        """
        Backspace one character in the current item on the stack. Return 0 if a
        character was backspaced, 1 if the whole item was wiped out, and -1 if
        a stack item was not being edited at all.
        """
        if not self.editing_last_item:
            return -1

        assert self.bos is not None, "Editing last item without an item on the stack"
        if self.cursor_posn == 1:  # remove the stack item in progress
            del self.bos
            return 1
        else:
            self.bos.backspace()
            self.cursor_posn -= 1
            return 0

    def clear(self):
        "Clear the stack."
        self.s.clear()
        self.stack_posn = -1
        self.cursor_posn = 0
        self.editing_last_item = False

    def enter_number(self, runningOp=None):
        """
        Finish the entry of a number.

        Return:
            True if a number was finished.
            False if bos was already finished.

        Raises:
            ValueError if the value was invalid and the number couldn't be
            finished. The exception message can be displayed on the status bar.

        Set runningOp to an operation name if you're entering prior to running
        an operation (go figure) for a more helpful error message in that case.
        """
        # Even if we were *not* editing the stack, checkpoint the stack state.
        # This ensures that we will get a checkpoint anytime we call an
        # operation as well as when we enter a number onto the stack.
        history.hs.checkpoint_stack(self)

        if self.editing_last_item:
            if self.s[self.stack_posn].finish_entry():
                self.editing_last_item = False
                self.cursor_posn = 0
                return True
            else:
                if runningOp:
                    msg = 'Cannot run "%s": invalid value on bos.' % runningOp
                else:
                    msg = 'Bottom of stack is not a valid number.'
                raise ValueError(msg)
        else:
            return False

    def has_push_space(self, spaces):
        return STACKDEPTH >= len(self.s) + spaces

    def push(self, vals):
        """
        Push an iterable of numbers onto the stack.
        """
        if not self.has_push_space(len(vals)):
            return False

        for i in vals:
            self.s.append(StackItem(decval=i))
        self.stack_posn += len(vals)
        return True

    def pop(self, num=1):
        """
        Pop /num/ numbers off the end of the stack and return them as a list.
        """
        self.stack_posn -= num
        oldStack = copy.deepcopy(self.s)
        try:
            return list(reversed([self.s.pop().decimal for _ in range(num)]))
        except IndexError:
            self.s = oldStack
            self.stack_posn += num
            return None

    def memento(self):
        """
        Generate a memento object for the current state of the stack.
        """
        return copy.deepcopy(self.__dict__)

    def restore(self, memento):
        """
        Restore the current object to a prior state checkpointed by calling
        memento().
        """
        self.__dict__.clear()
        self.__dict__.update(memento)
