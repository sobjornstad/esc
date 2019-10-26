=====
Menus
=====

Many :ref:`operations <Operations>` can go on the main menu,
but at some point you may want to create additional menus
or register new items on existing menus.

Menus can have submenus to an effectively infinite depth.


Creating new menus
==================

Menus are defined with the :func:`Menu <esc.commands.Menu>` constructor:

.. autofunction:: esc.commands.Menu

Example:

.. code-block:: python

    from esc.commands import Operation, Menu, main_menu

    qdoc = """
    This menu contains common operations needed when working with
    problems in queueing theory.
    """
    qmenu = Menu('Q', 'queueing menu', parent=main_menu, doc=qdoc)

    # Here we would define functions whose @Operation decorators
    # take 'qmenu' as their menu= argument.


Adding to existing menus
========================

Sometimes it's useful to extend menus defined by other plugins.
This poses a challenge: how do we get access to those menu objects?
The plugins directory is not a package and we can't guarantee its contents,
so it's tricky to import from other plugins.
The easiest method uses the :meth:`esc.commands.EscMenu.child()` method:

.. automethod:: esc.commands.EscMenu.child
    :noindex:

We only need to know the menu access keys
to get at any item from the main menu!
Let's suppose we want to add a ``secant`` operation
to the trig menu installed by the *trig* plugin bundled with esc.
In order to do that, we need to obtain the trig menu.
The key of this menu is ``t``.
Thus we would do:

.. code-block:: python

    from esc.commands import main_menu

    trig_menu = main_menu.child('t')

This isn't very robust, though.
We probably want to make sure we've actually gotten the trig menu
and not some other menu that happened to have the access key ``t``,
and we might want our plugin to add its own operations
even if we don't have the trig-menu plugin installed.
Let's add these features:

.. code-block:: python

    from esc.commands import main_menu
    from esc.oops import NotInMenuError, ProgrammingError

    if 't' in main_menu.children:
        trig_menu = main_menu.child('t')
        if trig_menu.description != 'trig menu':
            raise ProgrammingError(
                f"Expected the menu 't' to be the trig menu, but it was "
                f"{trig_menu.description}.")
    else:
        trig_doc = """
            Calculate the values of trigonometric functions, treating inputs as
            either degrees or radians depending on the mode.
        """
        trig_menu = Menu('t', 'trig menu', parent=main_menu,
                        doc=trig_doc,
                        mode_display=trig_mode_display)

This is better.
If the menu doesn't exist already, we'll create it;
if it does, we'll retrieve it and then be sure it's the right one,
throwing an error if it isn't.

.. warning::
    It's important to make sure your plugin loads
    *after* the plugin you're extending,
    or that plugin will crash when it tries to add a menu that already exists
    (unless it does the same check you did).
    That's easy enough to do
    by :ref:`changing the filename <Installing plugins>`
    to be alphabetically later than the plugin you're targeting;
    an easy way is to name your file
    as the target plugin with an additional suffix,
    like ``trigextensions.py``.
    (Don't use an underscore, though -- that sorts before the dot!)

.. note::
    A good future addition to esc would be a convenient way
    to remap the keys added by different plugins,
    since it's easy for them to end up colliding
    if they aren't designed with each other in mind.
    As of now, this is a bit hacky still
    and manual modification is required if you encounter a collision.
