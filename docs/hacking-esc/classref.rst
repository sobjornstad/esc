===============
Class Reference
===============

This page describes some miscellaneous classes
you may encounter while developing esc plugins
and want to know more about.
This is not an exhaustive reference to all of esc's classes;
for details on classes that plugin developers
do not come into contact with,
you'll want to dive into the source.


EscCommands
===========

.. currentmodule:: esc.commands

Anything that shows up on the :guilabel:`Commands` menu
has an associated instance of :class:`EscCommand`.
:class:`EscCommand` is subclassed as follows:

.. inheritance-diagram:: esc.commands esc.builtin_stubs
    :parts: 1


EscCommand subclasses
---------------------

.. autoclass:: EscCommand
    :members:

.. autoclass:: EscMenu
    :members:
    :show-inheritance:

.. autoclass:: EscOperation
    :members:
    :show-inheritance:

.. autoclass:: EscBuiltin
    :members:
    :show-inheritance:


Loading EscCommands
-------------------

:class:`EscCommand`\ s are loaded
by the :mod:`function_loader <esc.function_loader>`:

.. automodule:: esc.function_loader
    :members:

.. currentmodule:: esc.commands

The function loader imports the built-in functions file
and any function files in your :ref:`user config directory <Plugin location>`.
Importing a function file causes
calls to the constructors in :class:`EscCommand`
to be run (:func:`Operation`, :func:`Menu`, :func:`Constant`,
:func:`Mode`, and :func:`ModeChange`),
and these constructors in turn create :class:`EscCommand` instances
which are added to the :attr:`children <EscCommand.children>` attribute
of the main menu or a submenu of the main menu.


StackItems
==========

.. currentmodule:: esc.stack

:class:`StackItem`\ s are used to represent each number entered onto the stack.
Typically, you can request a Decimal or string representation of the stack item
in your operation functions
(see the documentation on parameter binding
in :func:`Operation <esc.commands.Operation>` for details).
If you need both in one function, you may want to work with the full object:

.. autoclass:: StackItem
    :members:

    .. note::
        By the time you receive a :class:`StackItem` in a plugin function,
        :attr:`is_entered <StackItem.is_entered>` should always be ``False``,
        so many of the following methods will not be applicable.


Registry
========

In general, you should prefer working solely with the stack
when writing operations,
rather than accessing :ref:`registers <Registers>`;
operations that use registers are harder to write
and harder for users to understand,
and any changes made to registers can't be undone.
(Working through the undo/redo history
will still deliver the correct values to the stack,
since undoing and redoing restores past states
rather than doing the calculations again,
but history entries might not match the current values of registers anymore,
and changes your operation makes to registers won't be undone/redone.)

However, sometimes it may be useful to use registers as parameters
or even as outputs in special-purpose custom operations.
*You should do this only if you fully understand the consequences
as described in the previous paragraph!*
In this case, you can provide a parameter called ``registry``,
and you will receive the following object:

.. autoclass:: esc.registers.Registry
    :members:
    :private-members:
    :special-members: __contains__, __len__, __getitem__, __setitem__, __delitem__
    :undoc-members:

.. warning::
    If you *set* a register in your operation,
    be sure to turn the ``simulate <esc.commands.Operation.simulate>``
    option off in your :func:`Operation <esc.commands.Operation>` decorator,
    or users may end up inadvertently setting registers
    when viewing the help for your function.


Exceptions
==========

The most important exceptions are described (and indexed) in the context
where you need to deal with them,
but here is the complete hierarchy for reference.

.. currentmodule:: esc.oops

.. inheritance-diagram:: EscError FunctionExecutionError
                         InsufficientItemsError ProgrammingError
                         FunctionProgrammingError InvalidNameError
                         NotInMenuError
    :parts: 1

.. autoclass:: EscError

.. autoclass:: FunctionExecutionError
    :noindex:

.. autoclass:: InsufficientItemsError
    :noindex:

.. autoclass:: ProgrammingError
    :noindex:

.. autoclass:: FunctionProgrammingError

.. autoclass:: InvalidNameError

.. autoclass:: NotInMenuError
