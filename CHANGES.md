Changes in 1.1.0
================

There are two major changes in 1.1.0.

First, **terminal size and layout** have been overhauled.
esc no longer crashes when the terminal is resized below its minimum size,
and instead shows a helpful message suggesting you make it larger.
The minimum size has also decreased to 60x16.
More space is used for the stack and history,
since registers essentially never need all the possible available space,
and esc will dynamically adjust the size of each container to something sensible
for the current screen size.

Combined with that, the stack now has infinite size in practice
(theoretically bounded by the memory available to the running app).
The stack window will only show the items at the bottom of the stack
that fit on the screen,
but all items further up will remain available by rolling the stack
or consuming some items at the bottom.
In practice, the 12-item stack was rarely a limitation,
but now if you temporarily need more items for some reason,
you can keep them.

Second, esc now supports **unit tags**,
which allow you to check your work with dimensional analysis.
Press `\` after entering a number to add a unit tag.
Subsequent arithmetic operations on these numbers will check, combine, and cancel
units as appropriate for those operations.
See the “Units” section of the user manual for details.

(Note that esc doesn't understand the actual meaning of units or convert units;
unit operations are purely symbolic.
Check out [Frink][] if your workflow uses units heavily
and you don't mind learning a small language.)

[Frink]: https://frinklang.org/

Custom operations in existing plugins that are not unit-aware will still work,
but using them will strip units from the inputs and push unitless values to the stack.
Operations can be upgraded to be unit-aware by adding a `unit_handling` parameter
to the `@Operation` decorator.
For many operations, this is simply a matter of selecting the correct built-in behavior;
for more complex ones, you can write a function
that describes the algebraic operations to be taken on the unit tags.
See the “Unit Handling” section of the developer manual for details.


Additional changes
------------------

* Python 3.10 or greater is now required.


Changes in 1.0.0
================

esc has been completely revamped in version 1.0.0. The philosophy and the user
interface are roughly the same, but the internals and the plugin API have
changed dramatically and the UI is improved.

In addition to major refactoring so I’m not embarrassed about the code and can
continue working on it without screaming, the most visible changes include:

* Python 3.6 or greater is now required.

* Functions have a new, more intuitive and pythonic API. Any logic you wrote in
  custom functions for version-0 esc will obviously still be applicable, but
  you’ll need to use the new @Operator decorator instead of registerFunction()
  calls, and the order of stack items and naming convention for arguments to
  your function have changed. If you were used to the old API, you should work
  through the [Operations section][] of the developer manual and upgrade any
  functions as needed.

* Functions you write can be automatically tested on application start.

* A new on-line help system can be accessed by pressing F1 and helps you
  understand in detail what each function does.

* You can now put user-defined functions in plugins (individual Python files) in
  a user config location, rather than having to edit the esc source
  distribution.

* The **History** and **Registers** sections of the screen now actually
  do something.

* Some functionality that was in base esc has been factored out into plugins so
  you can plug-and-play only the pieces you need and use.

* Decimal arithmetic is now used instead of floating-point, and precision is
  globally decreased to 12 significant figures, which prevents the
  stack window from overflowing with more digits than will ever be useful.

* A number of small, irritating bugs have been fixed.

* Complete [documentation][] has been published on Read The Docs.

* A PyPi package, `esc-calc`, is now available for easy installation.


[documentation]: https://esc-calc.readthedocs.io/en/
[Operations section]: https://esc-calc.readthedocs.io/en/master/hacking-esc/operations.html
