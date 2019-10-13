=========
Constants
=========

Adding new constants is easy as pi
with the :func:`Constant <esc.commands.Constant>` constructor:

.. autofunction:: esc.commands.Constant

The one trick here is that
if you want to add your constant to the constants menu,
you may not have access to the constants menu.
In this case, use the trick for
:ref:`adding to existing menus <Adding to existing menus>`:

.. code-block:: python

    from esc.commands import Constant, main_menu
    constants_menu = main_menu.child('i')
    Constant(299792458, 'c', 'speed of light (m/s)', constants_menu)

Since the constants menu is built in to esc,
``i`` will always be the constants menu
and there is no need to perform the other checks
described in the linked section.
