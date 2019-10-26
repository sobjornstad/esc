=========
Debugging
=========

If you do something wrong in a plugin,
a :class:`ProgrammingError <esc.oops.ProgrammingError>` will be raised:

.. autoclass:: esc.oops.ProgrammingError

The traceback will usually contain enough information to identify the problem.
If you have difficulty with the operation function itself
(rather than interacting with the esc framework),
you may wish to pull the function out into a test script
or use the ``logging`` standard library module,
as it can be quite challenging to debug a function
within the context of a curses app
without a separate connected debugger
(the terminal is taken over, precluding the use of ``print()`` statements
or a direct drop into ``pdb``).
One quick-and-dirty hack is to raise an ``Exception``
with a value you want to check as the message;
this will only let you check one value per run,
but it can still be useful.
