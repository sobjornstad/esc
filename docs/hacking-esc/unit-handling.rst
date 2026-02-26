=============
Unit Handling
=============

Custom operations can be made unit-aware
(see :ref:`Units <Units>` for information on unit tags in esc).
This is done through the ``unit_handling``
parameter to the :func:`@Operation <esc.commands.Operation>` decorator.

This parameter's value defaults to ``None``,
which evaluates to :attr:`UnitHandling.UNSPECIFIED <esc.units.UnitHandling.UNSPECIFIED>`.
That is, the operation does not define how to handle unitful quantities;
if the user tries to call it on unitful stack values,
they will get a warning, and if they choose to continue,
the calculation will be carried out unitless and the results will be unitless.

No matter how you configure an operation,
it's always valid to call the operation with all unitless inputs.
The unit handling behavior you choose is ignored in this case.


Built-in unit handling behaviors
================================

Many simple operations need only provide an appropriate
:class:`esc.units.UnitHandling` enum value to become unit-aware:

.. autoclass:: esc.units.UnitHandling
    :members:
    :member-order: bysource


Custom unit handling behaviors
==============================

For more complex operations,
or ones that push multiple values to the stack,
the result may not be distillable to a single default unit-handling behavior.
Here, you can instead pass a callable to ``unit_handling``
that performs the appropriate unit algebra calculations
used internally by esc.

This callable takes an array of :class:`UnitExpression <esc.units.UnitExpression>` s,
one for each of the inputs in sequence,
and should return an array of :class:`UnitExpression <esc.units.UnitExpression>` s,
one for each of the outputs in sequence.
See the class documentation for :class:`esc.units.UnitExpression` (below) for details.

esc does not verify that the unit algebra specified here
matches the algebra of your operation,
so it is a good idea to include a check of this behavior in your
:ref:`tests <Writing tests>`.

.. caution::
    esc allows a mix of unitful and unitless values to be passed
    to unit-aware operations.
    Whether this is sensible depends on the semantics of your operation.

    In many cases, it is valid and even required.
    For instance, some inputs may be semantically unitless while others are unitful,
    or the operation might be manipulating the stack without doing calculations
    (in which case you presumably just want to keep whatever units, or no units,
    were on that stack item before).

    However, if not attended to carefully,
    this behavior can lead to results with nonsensical units being pushed onto the stack
    without any warning.
    For instance, if you create a “velocity” operation that takes a distance and a time,
    define its unit_handling as ``lambda u: u[0].multiply(u[1])``,
    and the user passes ``5`` for the distance and ``3 seconds`` for the time,
    the result will be ``15 seconds``, which is obviously not a valid velocity.

    If a mix of unitful and unitless values is not sensible,
    or only certain combinations of unitful and unitless values are sensible,
    your unit handler should check for this condition
    and raise a :class:`UnitlessOperandError <esc.oops.UnitlessOperandError>`.
    The user will be able to override this by pressing the operation key again,
    and the resulting values will be unitless.

.. autoclass:: esc.units.UnitExpression
    :members:
    :member-order: bysource


Example
-------

Consider the following operation,
which calculates the distance traveled and final velocity
for an object starting from rest under constant acceleration:

.. code-block:: python

    def distance_velocity_unit_handler(units):
        if (not all(u.is_unitless for u in units)) and any(u.is_unitless for u in units):
            raise UnitlessOperandError()
        return [
            units[0].multiply(units[1]).multiply(units[1]),
            units[0].multiply(units[1]),
        ]

    @Operation(key='a', menu=main_menu, push=2, 
               description='dist/vel',
               log_as="accel {0} for {1}: travels {2} and reaches {3}",
               unit_handling=distance_velocity_unit_handler)
    def distance_and_final_velocity_from_standing(acceleration, time):
        return [
            time * time * acceleration / 2,
            time * acceleration,
        ]
