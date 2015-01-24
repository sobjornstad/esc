About esc
=========

esc (pronounced /esk/) is an Extensible Stack-based Calculator which runs in a
terminal using curses. What does this mean?

* esc is *stack-based*, operating using a Reverse Polish Notation (RPN)-like
  syntax. Rather than typing `2 + 2`, you enter the two numbers **2** and **2**
  onto the stack, then use the **+** function to add them. This can be slightly
  awkward at first, but for most people becomes more efficient and elegant than
  the standard method with a small amount of practice.

* esc is *extensible*. If you frequently need to multiply two numbers together,
  add five, and then divide the result by pi, you can add a function to the
  calculator to do this using a single line of Python code. That is not an
  exaggeration and does not involve any tricks, and you can learn how to do it
  in a few minutes in the `extending.md` page of the documentation. The
  extension features are simple enough to be accessible even to people who do
  not know Python or do not have prior programming experience.

* esc is *fast*, *simple*, and *terminal-based*. All you need is an 80x24
  terminal and your keyboard.

esc should run on Unix-like systems and Mac OS X; the required `curses` module
is not available on Windows versions of Python, but esc should work in Cygwin.

**esc is currently alpha software.** It calculates correctly and operates as
expected, but there are a few noticeable missing features, such as the large
windows labeled “history” and “registers” that do not yet do anything. The
documentation is also a work in progress, although in my opinion it is still
better than the documentation of some software that is allegedly completed.

Manual
======

There are three documentation files located in the `docs/` folder:
* **beginners.md** – this contains information about understanding the stack and
  Reverse Polish Notation. If you have used another RPN calculator before, you
  can skip this, but users new to RPN should read this first.
* **manual.md** – this contains the user documentation for the program. You
  should read this next, or first if you skipped the first file.
* **extending.md** – this contains the “developer documentation”, although every
  user of this calculator can easily be a “developer” if they so desire. In here
  you will learn how to add new functions and change the menus of your esc
  calculator using simple Python code.
