=====
Modes
=====

*Modes* are global state that can be used to allow esc operations
to work in different ways.
For instance, the trig operations in the *trig* plugin distributed with esc
use a degrees/radians mode.
Modes tend to be confusing to both users and programmers,
so it's best to avoid them when possible,
but sometimes it's difficult to do without them
(do you really want to create and select
a whole separate set of trig operations
depending on whether you're calculating in degrees or radians?).

Working with modes
==================

Modes are created using the :class:`Mode <esc.commands.Mode>`
and :class:`ModeChange <esc.commands.ModeChange>` constructors:

.. autofunction:: esc.commands.Mode

.. autofunction:: esc.commands.ModeChange

Aside from defining :class:`ModeChange` operations,
you can view and edit the values of modes
using the :mod:`modes <esc.modes>` module:

.. automodule:: esc.modes
    :members:


You'll probably want to display the value of your mode somewhere
-- as confusing as modes can be already,
they're even worse when they're invisible!
Typically, this is done by supplying a ``mode_display`` callable
to the :class:`Menu <esc.commands.Menu>`
that contains the associated operations.
This callable takes no arguments
and calls :meth:`modes.get <esc.modes.get>` to determine the display value:

.. code-block:: python

    def my_mode_display_1():
        # Assumes the values of the mode are strings.
        # If they're something else, you need to map them to strings here.
        return modes.get('my_mode')


Example
=======

Here's a complete silly example:

.. code-block:: python

    from esc.commands import Operation, Mode, ModeChange, Menu, main_menu, BINOP
    from esc import modes

    def opposite_mode():
        return "[opposite day]" if modes.get('opposite_day') else ""
    bool_menu = Menu('b', 'boolean functions', parent=main_menu, doc="blah",
                     mode_display=opposite_mode)

    Mode('opposite_day', False, (True, False))
    ModeChange("o", "enable opposite day", menu=bool_menu,
               mode_name='opposite_day', to_value=True)
    ModeChange("O", "disable opposite day", menu=bool_menu,
               mode_name='opposite_day', to_value=False)

    @Operation('a', menu=bool_menu, push=1,
               description="AND sos and bos",
               log_as=BINOP)
    def and_(x, y):
        result = x and y
        return int((not result) if modes.get('opposite_day') else result)

    # ...insert other boolean functions here
