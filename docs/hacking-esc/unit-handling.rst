=============
Unit Handling
=============

Custom operations can be made unit-aware
(see :ref:`Units <Units>` for information on unit tags in esc).
This is done through the ``unit_handling``
parameter to the :func:`@Operation <esc.commands.Operation>` decorator.

This parameter's value defaults to ``None``,
which gives unspecified behavior.
That is, the operation does not define how to handle unitful quantities;
if the user tries to call it on unitful stack values,
they will get a warning, and if they choose to continue,
the calculation will be carried out unitless and the results will be unitless.

No matter how you configure an operation,
it's always valid to call the operation with all unitless inputs.
The unit handling behavior you choose is ignored in this case.


Built-in unit handling behaviors
================================

Many simple operations can become unit-aware
by choosing an appropriate built-in unit handling behavior from :mod:`esc.units`.
Simply set unit_handler to a newly constructed instance of one of these handler classes
(e.g., ``unit_handler=additive_unit_handling()``):

.. autoclass:: esc.units.additive_unit_handling
   :no-members:

.. autoclass:: esc.units.multiplicative_unit_handling
   :no-members:

.. autoclass:: esc.units.divisive_unit_handling
   :no-members:

.. autoclass:: esc.units.power_unit_handling
   :no-members:

.. autoclass:: esc.units.root_unit_handling
   :no-members:

.. autoclass:: esc.units.preserve_unit_handling
   :no-members:

.. autoclass:: esc.units.no_output_unit_handling
   :no-members:

.. autoclass:: esc.units.no_input_unit_handling
   :no-members:

.. autoclass:: esc.units.unspecified_unit_handling
   :no-members:


Custom unit handling behaviors
==============================

For more complex operations,
or ones that push multiple values to the stack,
the result may not be distillable to a single default unit-handling behavior.
Here, you can instead pass a custom
:class:`UnitHandler <esc.units.UnitHandler>` callable for ``unit_handling``.
While the built-in behaviors
use subclasses of :class:`UnitHandler <esc.units.UnitHandler>`
for clarity of interface, structure, and customizability,
if you're writing a one-off unit handler for an operation,
you will likely want to just write a single function with the appropriate parameters.

.. autoclass:: esc.units.UnitHandler
    :members:

Inside your callable, you will ordinarily use the methods on the
:class:`UnitExpression <esc.units.UnitExpression>` objects passed as ``input_units``
to determine what units to return:

.. autoclass:: esc.units.UnitExpression
    :members:
    :member-order: bysource

esc does not verify that the unit algebra specified by a unit handler
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
    define the return value of your ``unit_handling`` as
    ``[input_units[0] / input_units[1]]``,
    and the user passes ``10`` for the distance and ``2 seconds`` for the time,
    the resulting “velocity” will be ``5 seconds^-1``,
    which is presumably not what either you or they expected.

    If a mix of unitful and unitless values is not sensible,
    or only certain combinations of unitful and unitless values are sensible,
    your unit handler should check for invalid conditions
    (using the :attr:`is_unitless` attribute of the unit object)
    and raise a :class:`UnitlessOperandError <esc.oops.UnitlessOperandError>`.
    The user will be able to override this by pressing the operation key again,
    which will carry out the calculation without units.


Example
-------

Consider the following operation,
which calculates the distance traveled and final velocity
for an object starting from rest under constant acceleration:

.. code-block:: python

    from esc.oops import UnitlessOperandError
    from esc.units import UnitHandler

    def distance_velocity_unit_handler(input_units):
        """acceleration, time -> distance, velocity"""
        if ((not all(u.is_unitless for u in input_units))
                and any(u.is_unitless for u in input_units)):
            raise UnitlessOperandError()
        return [
            input_units[0] * input_units[1] * input_units[1],
            input_units[0] * input_units[1],
        ]

    @Operation(key='a', menu=main_menu, push=2,
                description='dist/vel',
                log_as="accel {0} for {1}: travels {2} and reaches {3}",
                unit_handling=distance_velocity_unit_handler)
    def distance_and_final_velocity_from_standing(acceleration, time):
        """
        Given a constant acceleration and an amount of time,
        calculate the distance traveled and the final velocity
        of an object starting from rest.
        """
        return [
            time * time * acceleration / 2,
            time * acceleration,
        ]


You could equivalently write the unit handler as a subclass of
:class:`UnitHandler <esc.units.UnitHandler>`.

.. code-block:: python

    class distance_velocity_unit_handler(UnitHandler):
        description = "acceleration, time -> distance, velocity"

        def __call__(self, input_units):
            if ((not all(u.is_unitless for u in input_units))
                    and any(u.is_unitless for u in input_units)):
                raise UnitlessOperandError()
            return [
                input_units[0] * input_units[1] * input_units[1],
                input_units[0] * input_units[1],
            ]
