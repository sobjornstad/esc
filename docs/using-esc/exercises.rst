=========
Exercises
=========

To get the hang of using esc and Reverse Polish Notation,
here are a few simple exercises you can work through.
Click the footnote link to show the answer.


Questions
=========

Calculate the answers to the following algebraic expressions:

1. :math:`2 + 5` [1]_
2. :math:`17 / 5` [2]_
3. :math:`\frac{30}{3 \cdot 5}` [3]_
4. :math:`60(2 \cdot (17 + 8))(5 \cdot 3)` [4]_
5. :math:`\frac{12 + 6}{18 \mod 3}` [5]_
6. :math:`\frac{1.52 \times 10^3}{12^{-2}}` [6]_

Enter the numbers listed in the left column into the stack,
then manipulate it using arithmetic or stack functions or registers
to match the right column.
You *cannot* enter any new numbers by typing them.

.. list-table::
    :header-rows: 1

    * - Answer
      - Initial stack
      - Final stack
    * - [7]_
      - | 5
        | 3
      - | 3
        | 5
    * - [8]_
      - | 1
        | 2
        | 3
      - (empty)
    * - [9]_
      - | 1
        | 2
        | 3
      - | 3
        | 1
        | 2
    * - [10]_
      - | 1
        | 2
        | 8
      - | 11
        | 16
        | 8


Answers
=======

There are an infinite number of possible entry sequences
that would work for every question.
The sequence or sequences shown here are just some sensible choices;
obviously, the most important thing is that you have the right answer.

In many cases, you'll have a choice
between entering the numbers in strict order as they come in the expression
or working from the inner parentheses out,
or some combination thereof.
This is largely a matter of taste,
although in extremely large calculations
you could run out of stack space if you type the numbers in order.
This is not a serious threat in esc since the stack holds at least 12 numbers,
but is more of a concern on hardware RPN calculators,
which may hold as few as 3.

.. note::
    Keystroke sequences are rendered with spaces between every keystroke
    for readability here.
    Many of these spaces are not necessary when typing into esc
    or will even give the error "No number to finish adding".

.. [1] **7** (``2 5 +``)

.. [2] **3.4**
       (``17 5 /``)

.. [3] **2**
       (``30 3 5 * /``
       or ``3 5 * 30 x /``)

.. [4] **244800**
       (``60 2 17 8 + * * 5 3 * *``
       or ``17 8 + 2 * 60 * 5 3 * *``)

.. [5] Trick question, this was a **division by zero error**!
       (``12 6 + 18 3 % /``)

.. [6] **218880**
       (``1.52e3 12 _2 ^ *``)

.. [7] ``x``

.. [8] ``c``

.. [9] ``x y p x ^V``, where ^V means to paste into esc!

.. [10] ``>x + + <x d + <x``
