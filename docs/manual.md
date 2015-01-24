manual.md – user documentation for esc

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
key, 5 would be popped first and used as the first argument and you would get
the answer -2, which would be confusing.*

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
well as the numerals:

* **.**: Enter a decimal point.
* **_**: Enter a negative sign. (You can’t use **-** for this because it would
  try to perform subtraction on the stack.)
* **e**: Enter scientific notation, like `2.65e6` for 2.65 X 10^6. This can be
  combined with `\_` to enter a negative power.

esc will not prevent you from typing these keys in an order that makes no sense;
for instance, you could type `2-.6ee8-` into the stack window. However, if you
try to press Enter or perform an operation, esc will refuse to do it until you
change the entry to something valid.

Undo
====

Every time you enter a number onto the stack or perform an operation, esc saves
the contents of the stack. To go back to a previous version, press **u**. You
can undo all the way back to the beginning of the session if you like.

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

There are only so many keys on the keyboard and only so much space in the
commands window, so it is useful to move functions which are less frequently
used onto menus. There are three menus by default: the trig menu, the log menu,
and the insert constant menu (which is slightly different and will be discussed
momentarily).

Menus appear like any other command in the commands window (except that they
usually have the word “menu” in their description). When you press the access
key, however, they change the contents of the command window rather than
directly taking an action. The status bar will also inform you of this, and the
cursor will move to the bracketed indicator to indicate that your input is no
longer going to the stack. Pressing `q` will always close the menu, no matter
which menu you’re on, as will pressing any key that is not listed on the menu
(albeit accompanied by an error message). Selecting any of the menu choices will
carry out the appropriate operation, just as if it had been listed on and
selected from the main menu.

The *constants menu* is special because instead of popping things off the stack
and calculating with them, the items in this menu simply push one value – the
specified constant – onto the stack. By default, only pi and e are listed, but
it is extremely easy to add your own constants.

Conclusion
==========

After reading this file, you should be able to use esc for all of your numerical
calculating needs. (esc is designed to be *simple*, and as such is not going to
be automatically solving your calculus problems for you anytime soon!)

When you’re comfortable with this and are ready to start increasing your
efficiency with the power of esc’s extensibility, dive into the `extending.md`
file.
