Introduction
============

esc is an Extensible Stack-based Calculator which runs in a terminal using
curses. What does this mean?

* esc is *stack-based*, operating using a Reverse Polish Notation (RPN)-like
  syntax. Rather than typing `2 + 2`, you enter the two numbers **2** and **2**
  onto the stack, then use the **+** function to add them. This can be slightly
  awkward at first, but for most people becomes more efficient and elegant than
  the standard method with a small amount of practice.

* esc is *extensible*. If you frequently need to multiply two numbers together,
  add five, and then divide the result by pi, you can add a function to the
  calculator to do this using a single line of Python code. That is not an
  exaggeration and does not involve any tricks, and you will see how to do it
  later. The extension features are simple enough to be accessible even to
  people who do not know Python or do not have prior programming experience.

* esc is *fast*, *simple*, and *terminal-based*. All you need is an 80x24
  terminal and your keyboard.

esc should run on Unix-like systems and Mac OS X; the curses module is not
included in Windows versions of Python, but it should work in Cygwin.

**esc is currently alpha software.** It calculates correctly and operates as
expected, but there are a few noticeable missing features, such as the large
windows labeled “history” and “registers” that do not yet do anything. This
documentation is also a work in progress.

Understanding the Stack
=======================
If you’ve ever used a RPN-based calculator or calculator program, you can
probably skip this section if you like, as you’ll be right at home with this
part.

When you start esc, you will see a status bar and four windows, *Stack*,
*History*, *Commands*, and *Registers*. The most important window is the stack.
This is where you type in the numbers you want to work with and where you get
your results.

As long as no other operation is in progress, your cursor will be positioned in
the stack window. To enter a number on the stack (this is called *pushing it
onto* the stack), simply start typing the number. The indicator at the left of
the status bar will change to `[i]` to indicate that you’re inserting a number,
and the numbers will appear in the stack window. When you’re done typing the
number, press Enter or the spacebar; the cursor will move to the next line of
the stack.

You can enter as many numbers as you like this way, at least until the stack
fills up. (In esc, the stack size is based on the number of lines allocated for
the stack on the screen, which is ordinarily 12. 12 entries should be more than
enough for all but the craziest calculations; many RPN-based HP calculators only
have four, and that is usually enough.)

Eventually you probably want to actually perform some operation on the contents
of the stack. In the *Commands* window, you will see a list of operations that
you can perform. At the very top are listed the typical arithmetic operations:
addition, subtraction, multiplication, division, exponentiation, modulus
(remainder), and square root (‘s’). To perform one of these operations, simply
press the associated key. For instance, to perform addition, you press `+`.

When you perform an operation, it removes a certain number of entries from the
bottom of the stack (this is called *popping them off* the stack). It then uses
those values to calculate the result and pushes the result back onto the bottom
of the stack. If your stack reads 1, 2 and 3 (from top to bottom) and you press
the **+** key, the 1 is untouched, while the 2 and 3 are removed from the stack
and the answer, 5, pushed on, so that the stack now has two entries, 1 and 5.

Most operations pop one or two items from the stack and push one answer.
However, this is not a requirement; an operator could pop four values and push
two back. (None of the default functions do anything this complicated.)

It is not actually necessary to press Enter after every number you place on the
stack. If you enter a number and then wish to immediately enter another number,
you will need to press Enter (or the spacebar), since esc has no way of knowing
where one number stops and the second begins without it. But if you type a
number and then wish to perform an operation, you can simply press the operator,
and esc will finish entering the number automatically before it tries to perform
the operation.

If you haven’t done so already, play around with pushing values onto the stack
and running operations on them for a while until you get the hang of it. It’s
also useful to try writing down some algebraic expressions, such as `6 * (3 + 4)
/ (8 * (6 + 3))` and calculating out the answers. If you have trouble figuring this
out, there are a number of tutorials online that explain how to enter the
numbers, which you can find by searching for “reverse polish notation.”

Stack Abbreviations and Operations
==================================

There are three abbreviations which are used throughout esc’s interface and this
documentation, which describe values on the stack:

* **bos**, “bottom of stack.” This number is the last line displayed on the
  screen, moving from top to bottom, and is the first number that will be popped
  off the stack.
* **sos**, “second on stack.” This is the number displayed immediately above
  bos.
* **tos**, “top of stack.” This number is rarely actually accessed, because
  ordinarily values are removed and added from the *bottom* of the stack, not
  the top. However, it does get referenced occasionally.

*Note: If you are familiar with stacks from computer science, you may be puzzled
as to why esc pushes and pops from the *bottom* of the stack, as opposed to the
more normal top. The answer is that if you do it this way, non-commutative
operations appear on the screen in the correct order. If numbers were popped
from the top of the stack, you would see 5 above 7, but when you pressed the -
key, 5 would be popped first and you would get -2, which would be confusing.*

As you play with the stack, adding numbers and performing operations, you will
eventually want to get rid of parts of the stack, or perhaps duplicate or
exchange them. There are a number of *stack operations* that serve this need,
which are displayed in the commands window by default:

* **duplicate bos**: Push a copy of the bottommost entry onto the stack. (A
  simple application of this is squaring the bottommost number: press `d\*`.)
* **exchange bos, sos**: Swap the bottom two entries on the stack. This is
  useful with non-commutative operations: if you mean to divide 6 by 2 but enter
  2 before 6 (or the answers appear on the stack in that order as the result of
  other operations), you can use this operation to put them in the correct
  order.
* **pop off bos**: Pop the value at the bottom of the stack and discard it.
* **roll off tos**: Discard the value at the *top* of the stack, “rolling” the
  other values up by one.
* **clear stack**: Delete the entire contents of the stack.


Complex Input
=============

To enter things other than natural numbers, you will need the following keys as
well as the numbers:

* **.**: Enter a decimal point.
* **_**: Enter a negative sign. (You can’t use **-** for this because it would
  try to perform subtraction on the stack.)
* **e**: Enter scientific notation, like `2.65e6` for 2.65 X 10^6. This can be
  combined with `_` to enter a negative power.

esc will not prevent you from typing these keys in an order that makes no sense;
for instance, you could enter `2-.6ee8-` into the stack window. However, if you
try to press Enter or perform an operation, esc will refuse to do it until you
change the entry to something valid.

Undo
====

Every time you enter a number onto the stack or perform an operation, esc saves
the current state of the stack. To go back to a previous version, press **u**.
You can undo all the way back to the beginning of the session if you like.

If you undo too far or you just wanted to go back temporarily, press **Ctrl-R**
to redo. You can redo until you enter another number or use an operation. (You
have to actually *enter* the number to remove the possibility of redo; you can
edit a number without pressing Enter or an operation key and still use Ctrl-R.)

This feature is entirely lacking on most calculators and calculator apps, which
is quite remarkable given its obvious utility. (Some calculators have an option
to recall the last expression and edit it, but this doesn’t restore any
variables, such as the previous answer, so it doesn’t always work.)

Menus
=====
