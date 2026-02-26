=====
Units
=====

esc allows you to add a **unit tag** to any number on the stack.
esc does not understand the meaning of units or offer automatic conversion,
but it will do symbolic dimensional analysis on them
to help you check your work.

To attach a unit tag to a number, type a backslash (:kbd:`\\`) after it,
then type the unit tag.
Unit names can consist of letters, numbers,
and symbols other than ``*``, ``/``, or ``^``.
``*`` and ``/`` are used to create compound units (e.g., ``kg / liters``),
while ``^`` allows you to raise a unit to an integer power (e.g., ``feet^2``).
Negative powers represent reciprocals (e.g., ``seconds^-1``).

esc recognizes plurals formed with a suffix ``s``,
so that ``second`` and ``seconds`` will be treated as equivalent,
but otherwise it does not know about equivalent forms
like ``feet`` and ``foot`` and ``ft``,
or ``m`` and ``meter``,
so you should be consistent;
esc generally recommends using either the abbreviation or the plural form of the unit
throughout your calculations.

To finish entering a unit tag, press :kbd:`Enter` or :kbd:`Space`.
You can overwrite the unit tag of the previous item on the stack
by pressing :kbd:`\\` again;
immediately following :kbd:`\\` with :kbd:`Enter` or :kbd:`Space`
will remove the unit tag.

A number with a unit tag attached is called a **unitful quantity**,
while a number without one is called a **unitless quantity**.


Operations on unitful quantities
================================

When you run an operation and at least one of its inputs has a unit tag,
esc will check that the operation is well-defined
and combine the units as appropriate.

When **multiplying, dividing, exponentiating, or taking roots**,
esc will combine and cancel units.
For instance, multiplying a quantity in ``meters / second`` by a quantity in ``seconds``
will result in a quantity in ``meters``,
while dividing a quantity in ``widgets / person`` by a quantity in ``hours``
will result in a quantity in ``widgets / person * hours``.

Multiplying or dividing a unitful quantity by a unitless quantity other than 1
(or vice versa)
will issue a warning :guilabel:`Mixing unitful and unitless operands`.
This is informational only, to remind you to check
that you didn't merely forget to type the appropriate unit.
If you're actually multiplying or dividing by a unitless quantity
(e.g., pi, a percentage, or an angle in radians),
simply press the operation key again to continue.

When **adding or subtracting quantities**,
esc will require them to have the same units.
Adding or subtracting quantities with different units
(or a unitless quantity and a unitful quantity)
will issue the error :guilabel:`Incommensurable units`.
You can override this error by pressing the operation key again;
this will ignore the units and return a unitless result.

Custom operations can define what combinations of units they accept
and what effect the input units have on the result units;
see the developer guide for details.
If a custom operation doesn't specify how to handle units,
the warning :guilabel:`This operation will remove units` will be issued
when you run it on unitful stack values;
pressing the operation key again
will pass the values as unitless and return a unitless result.
