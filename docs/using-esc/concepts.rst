========
Concepts
========

When you start esc, you will see a status bar and four windows:
:guilabel:`Stack`,
:guilabel:`History`,
:guilabel:`Commands`,
and :guilabel:`Registers`.
These windows match up neatly with the important concepts in esc.

.. figure:: images/esc.*
    :align: center

    A typical esc window at startup.


Stack
=====

The stack contains a series of numbers you are currently working with.
Almost all commands follow the pattern of:

1. read numbers from the stack;
2. do something with them;
3. return other numbers to the stack.

As long as no other operation is in progress,
your cursor will be positioned in the :guilabel:`Stack` window.
To enter a new number (this is called *pushing it onto* the stack),
simply start typing the number.
The indicator at the left of the status bar will change to ``[i]``
to indicate that you’re inserting a number,
and the numbers will appear in the stack window as you type.
When you’re done typing the number, press :kbd:`Enter` or :kbd:`Space`;
your cursor will then move to the next line of the stack.
If you make a typo, correct it with :kbd:`Backspace`.

.. figure:: images/entering-stack.*
    :align: center

    Entering several numbers onto the stack.

You can enter as many numbers as you like this way,
at least until the stack fills up.
(In esc, the stack size
is based on the number of lines allocated for the stack on the screen,
which is ordinarily 12.
12 entries should be more than enough for all but the craziest calculations;
many RPN-based HP calculators only have four, and that is normally enough.)

Enter negative signs with :kbd:`_` (underscore)
and scientific notation with :kbd:`e`
(e.g., ``3.66e11`` is 3.66 × 10^12 or 366,000,000,000).

.. tip::
    You need only press :kbd:`Enter` or :kbd:`Space`
    between consecutively typed numbers.
    If you type a number and then wish to
    perform an :ref:`operation <Arithmetic operations>`,
    you can simply press the key for the operator.
    For instance, typing ``2 2+``
    is equivalent to typing ``2 2 +``.



Commands
========

Arithmetic operations
---------------------

Eventually you'll probably get tired of typing in numbers
and want to actually perform some operation
on the contents of the stack.
In the :guilabel:`Commands` window,
you will see a list of operations that you can perform.
At the very top are listed the typical arithmetic operations.
To perform one of these operations,
simply press the associated key.
For instance, to perform addition, you press :kbd:`+`.

When you perform an operation,
it removes a certain number of entries from the bottom of the stack
(this is called *popping them off* the stack).
It then uses those values to calculate the result
and pushes the result back onto the bottom of the stack.
For example, if your stack is ``[1, 2, 3]``
and you press the :kbd:`+` key to add two numbers,
the ``1`` is untouched,
while the ``2`` and ``3`` are removed from the stack
and the answer, ``5``, is pushed on,
so that the stack now has two entries, 1 and 5.

.. note::
    Most operations pop one or two items from the stack and push one answer.
    However, this is not a requirement;
    an operator could pop four values and push two back.

    You can see how many and what values an operation pops and pushes
    in its :ref:`help page <Getting help on commands>`.

.. autofunction:: esc.functions.add
.. autofunction:: esc.functions.subtract
.. autofunction:: esc.functions.multiply
.. autofunction:: esc.functions.divide
.. autofunction:: esc.functions.exponentiate
.. autofunction:: esc.functions.modulus
.. autofunction:: esc.functions.sqrt


Stack operations
----------------

In addition to the arithmetic operations, some *stack operations* are provided.
These don't calculate anything but allow you to manipulate
the contents of the stack.

.. autofunction:: esc.functions.duplicate
.. autofunction:: esc.functions.exchange
.. autofunction:: esc.functions.pop
.. autofunction:: esc.functions.roll
.. autofunction:: esc.functions.clear


Menus
-----

Some entries in the :guilabel:`Commands` window
don't immediately do anything
but rather open a menu containing more commands,
much like on a desktop scientific calculator.
Simply choose an item from the menu to continue.


Other commands
--------------

In addition to the arithmetic and stack manipulation commands described above,
esc defines several special commands.

.. autofunction:: esc.functions.yank_bos


.. automodule:: esc.builtin_stubs

    .. autoclass:: esc.builtin_stubs.StoreRegister

        See :ref:`Registers` for more information on registers.

    .. autoclass:: esc.builtin_stubs.RetrieveRegister

        See :ref:`Registers` for more information on registers.

    .. autoclass:: esc.builtin_stubs.DeleteRegister

        See :ref:`Registers` for more information on registers.

    .. autoclass:: esc.builtin_stubs.Undo

        See :ref:`History` for more information on calculation history.

    .. autoclass:: esc.builtin_stubs.Redo

        See :ref:`History` for more information on calculation history.

    .. autoclass:: esc.builtin_stubs.Quit


Custom commands
---------------

In addition to all the commands described above,
you may see some other commands in your list at times.
These are added by :ref:`esc plugins <Plugins>`.


Getting help on commands
------------------------

esc has a built-in help system you can use to discover what a command does,
including the exact effect it would have on your current stack if you ran it.
Simply press :kbd:`F1`, then the key associated with the command.
If you choose a :ref:`menu <Menus>`, you'll get a description of the menu,
but you can also choose an item from the menu
to get specific help on that item.

.. figure:: images/divide-help.*
    :align: center
    :width: 80%

    Getting help on the division operation with several numbers on the stack.
    Press :kbd:`F1 /` to reach this screen.


History
=======

esc maintains a complete history of all the numbers you push onto the stack
and operations you perform.
The operations you execute and brief descriptions of their results
are displayed in the :guilabel:`History` window in the middle of the screen.

If you perform an operation and then want to back up,
simply choose :class:`Undo <esc.builtin_stubs.Undo>`.
To undo an undo, use :class:`Redo <esc.builtin_stubs.Redo>`.

Calculation history you can step through
is so useful it's amazing how few calculators offer it.


Registers
=========

In addition to placing numbers on the stack,
sometimes you might want to keep track of numbers
in a slightly more permanent way.
In this case, you can store the number to a register.


* To :class:`store to a register <esc.builtin_stubs.StoreRegister>`,
  press :kbd:`>`,
  then type an upper- or lowercase letter
  to name the register.
  The bottom item on the stack is copied into the :guilabel:`Registers` window.
* To :class:`retrieve the value of a register
  <esc.builtin_stubs.RetrieveRegister>`,
  press :kbd:`<`,
  then type the letter corresponding to the register
  whose value you want to retrieve.
  The value is copied into a new item at the bottom of a stack.
* To :class:`delete a register <esc.builtin_stubs.DeleteRegister>`,
  press :kbd:`X`,
  then type the letter of the register you want to delete.
  It is removed from the :guilabel:`Registers` window and its value is lost.

.. figure:: images/register-use.*
    :align: center
    :width: 80%

    Doing a few simple calculations,
    including placing some numbers in registers.

.. note::
    Registers do not participate in the undo/redo history.
    This is a feature, not a bug:
    a common esc workflow is to perform some calculation,
    then realize you needed those numbers again for something.
    You can store your answer to a register,
    then undo as needed to get those numbers back.
