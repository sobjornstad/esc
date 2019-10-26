==========
Operations
==========

The most common thing to do in a plugin is to add a new operation
(a.k.a. *function*).
This page describes how to do that.


Walkthrough
===========

In this walkthrough, we'll implement an operation on the main menu.
Our operation will calculate a proportion, like:

.. math::
    \frac{1}{2} = \frac{3}{x}

We'll pass the parameters in order,
so when the stack reads ``[1, 2, 3]``,
we will obtain 6.


Creating a plugin
-----------------

Create a new file in your :ref:`esc plugins directory <Plugin location>`
and paste in the following template:

.. code-block:: python

    """
    {name}.py - {description}
    Copyright (c) 2019 {your name}.

    {additional details}
    """

    from esc.commands import Operation, main_menu

Change the sections in brackets to appropriate values for your plugins.
Of course, the docstring is just a suggestion.
Reload esc and ensure no errors occur.
If you do get an exception, you probably made a syntax error;
fix the file as necessary to resolve it.


Writing a function
------------------

Operations are Python functions decorated with ``@Operation``.
We'll start with the function and then look at the decorator.

How should we write this function?
Let's generalize the example of a proportion calculation above,
where *d* is the number we're solving for:

.. math::
    \begin{align}
    \frac{a}{b} &= \frac{c}{d}\\
    bc &= ad\\
    d &= \frac{bc}{a}\\
    \end{align}

We'll go ahead and use these letters for our variable names;
they'll serve as well as anything else
since this is a very general operation
that could be used for just about anything.
Translating the algebraic notation above into Python:

.. code-block:: python

    def proportion(a, b, c):
        return b * c / a

Note that we can specify any number of parameters we want here
and name them anything we want,
and esc will check the parameter list to see how many stack items we need,
slice that many items off the bottom of the stack,
and bind them to the parameters in order.
(The details are somewhat more complicated;
see the documentation
for the :func:`@Operation <esc.commands.Operation>` decorator for more.)

.. note::
    esc uses the `Decimal`_ library to implement decimal arithmetic
    similar to that of many handheld calculators.
    All function arguments are thus Decimal objects.
    Most operations on Decimals yield other Decimals,
    so you probably will not even notice if you're doing normal arithmetic
    on your arguments.
    If you ever get confused, check out the linked library documentation.

    Return values from functions may be Decimal objects
    or any type that can be converted to a Decimal
    (string, integer, or float).
    Beware of returning floats except for numbers that are already irrational,
    as *all* the precision will be kept
    when converting back to the internal Decimal representation,
    even the rounding error inherent in binary floating-point values,
    which may result in silly values like ``1.000000000083``
    appearing on the stack.
    If your function includes non-integer constants,
    it's a good idea to use the Decimal constructor for them.

.. _Decimal: https://docs.python.org/3/library/decimal.html


Registering a function
----------------------

If you save the file and start esc, you won't get any errors,
but you won't have any new operations either.
In order to get an operation to show up,
we need to add the ``@Operation`` decorator described earlier.
That will look like this:

.. code-block:: python

    @Operation(key='P', menu=main_menu, push=1,
               description="proportion from abc",
               log_as="{0}:{1} :: {2}:[{3}]")
    def proportion(a, b, c):
        """
        Quickly calculate a proportion.
        If the bottom three items on the stack are A, B, and C,
        then calculate D where A : B = C : D.
        """
        return b * c / a

Most of this is probably fairly self-explanatory,
but a couple of points are worth noting.

* ``log_as`` is a format string whose positional placeholders will be replaced
  with a chain of the arguments to the function
  and the return values from the function.
  The formatted version will be used in the history window and help system.
* The function's docstring is used as the description in the help system.

``@Operation`` can get more complicated,
so without further ado here are the dirty details:

.. autofunction:: esc.commands.Operation


Creating tests
--------------

You probably don't want a calculator that returns the wrong results,
so it's important to test your custom function!
You could simply load esc and try it out,
and that's a good idea regardless,
but esc also offers built-in tests.
These tests run automatically every time esc starts up;
if they ever fail, esc will raise
a :class:`ProgrammingError <esc.oops.ProgrammingError>` and refuse to load.
This way, even if a new version of esc
makes breaking changes you don't know about
or you accidentally modify and break your function,
you can be confident that esc won't return incorrect results
(at least to the extent of your test coverage).

We can define automatic tests using the ``ensure`` attribute
which the ``@Operation`` decorator adds to our function.
Let's define a test that tests
the example we discussed at the start of this page:

.. code-block:: python

    proportion.ensure(before=[1, 2, 3], after=[6])

Let's test an error condition too.
What happens if calculating our proportion requires a divide by zero?
Without special-casing that in our function,
we would hope it informs the user that she can't divide by zero,
which esc does by raising a ``ZeroDivisionError``
which is caught by the interface.

.. code-block:: python

    proportion.ensure(before=[0, 2, 3], raises=ZeroDivisionError)

And it's that easy.
If you don't get a :class:`ProgrammingError <esc.oops.ProgrammingError>`
after restarting esc, your tests pass.

Here's the full scoop on defining tests:

.. autoclass:: esc.functest.TestCase


Putting it all together
-----------------------

Launch esc again.
If you've made any mistakes, esc will hopefully catch them for you here
and describe why you have an error or your test failed.
Type in three values that can be used to calculate a proportion,
choose the function from the menu,
and you should be set!


Error handling
==============

esc handles many kinds of errors that could occur in your functions for you:

* If there aren't enough items on the stack to bind to all your arguments,
  your function won't even be called
  and the user will be told there aren't enough items on the stack.
* If your function raises a ``ValueError``,
  the user will be informed a domain error has occurred
  (many math functions raise this exception in this case).
* If your function raises a ``ZeroDivisionError``,
  the user will be informed he cannot divide by zero.
* If your function raises a Decimal ``InvalidOperation``,
  the user will be informed the result is undefined.
  (The Decimal library in esc is configured
  so that ``Infinity`` is a valid result
  which occurs when extremely large numbers are put together
  such that the available precision is exceeded,
  but any result that would return ``NaN`` like ``0 / 0``
  raises ``InvalidOperation``.)

However, at times this will not be sufficient.
One of the most common cases occurs
when you need to work with the entire stack.
In this case, you need to check yourself to see if there are sufficient items,
as esc doesn't know how many you need.
To do so, simply check the length of your ``*args`` tuple
and raise an :class:`InsufficientItemsError <esc.oops.InsufficientItemsError>`
if it's too short:

.. code-block:: python

    def my_operation(*stack):
        if len(stack) < 2:
            raise InsufficientItemsError(number_required=2)
        # do stuff

.. autoclass:: esc.oops.InsufficientItemsError

Another case arises when your function encounters some arbitrary condition
that prevents it from continuing.
As a silly example, perhaps the result of your formula is undefined
if the sum of its input values is 6.
Raising a :class:`FunctionExecutionError <esc.oops.FunctionExecutionError>`
with a message argument will cause the function's execution to stop
and the message to be printed to the status bar.
(The stack will remain unchanged.)
As noted below, the message should be concise so it fits in the status bar
-- it will be truncated if it doesn't fit.

.. code-block:: python

    def my_operation(sos, bos):
        if sos + bos == 6:
            raise FunctionExecutionError("I don't like the number 6.")
        # do stuff

.. autoclass:: esc.oops.FunctionExecutionError

.. warning::
    If you do something complicated in your function
    that could result in an exception other than the types listed above,
    be aware that if you let an exception of another type
    bubble up from your function, esc will crash.
    This is generally reasonable behavior if you don't expect the error,
    since it makes it easy to spot and fix the problem,
    but if the error is an expected possibility you'll probably want to catch it
    and give the user a helpful error message describing the problem
    by raising a :class:`FunctionExecutionError <esc.oops.FunctionExecutionError>`.
