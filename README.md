What is esc?
============

**esc** (pronounced /esk/) is an Extensible Stack-based Calculator
designed for efficiency and customizability.
What does this mean?

* esc is *stack-based*,
  operating using a [Reverse Polish Notation][]-like syntax.
  Rather than typing `2 + 2` and pressing an equals key,
  you enter the two numbers `2` and `2` onto the stack,
  then choose `+` to add them.
  This can be slightly awkward at first,
  but it means no parentheses are necessary,
  and for most people it becomes faster and more elegant
  than the standard algebraic method
  with a small amount of practice.
  In addition, it is considerably easier to customize and program.

* esc is *extensible*.
  If you frequently need to
  multiply two numbers together, add five, and then divide the result by pi,
  you can add an operation to the calculator to do this specific operation
  using a couple of lines of Python code.
  The extension features are simple enough to be accessible
  even to people who do not know Python
  or have little to no programming experience.

  esc operations are arbitrary Python code, so if you want to get fancy,
  they can get arbitrarily complicated.
  You can even call APIs to perform calculations or get data!

* esc is *fast*, *simple*, and *terminal-based*.
  All you need is a working terminal (at least 80×24)
  and your keyboard.

[Reverse Polish Notation]: https://en.wikipedia.org/wiki/Reverse_Polish_notation


Installation
============

esc requires Python 3.6 or greater.
It is lightweight and has no dependencies outside the standard library
(except on Windows, where ``ncurses`` isn't available by default
and the ``windows-curses`` package is transparently installed to fix that).
The recommended installation method is through pip:

    $ pip install --user esc-calc

This will install an `esc` command to your system path which will launch esc.

After installing esc, you may wish to install plugins
(see the "Plugins" section in the [user guide](#documentation)).
Official plugins can be downloaded
from the `esc-plugins` folder of this repository.


Development
-----------

For development, clone this repository,
build a virtualenv with the necessary development tools,
and install esc into it:

    $ git clone https://github.com/sobjornstad/esc
    $ cd esc
    $ virtualenv --python=python3.7 venv  # or 3.6 if you don't have 3.7
    $ . venv/bin/activate
    $ pip install -r requirements.txt
    $ pip install -e esc
    $ esc


Documentation
=============

The user manual and API documentation on writing plugins for esc
are maintained on [Read The Docs][].

[Read The Docs]: https://esc-calc.readthedocs.io


Contributing
============

Bug reports, suggestions, and code contributions are welcome.

In particular,
if you write a plugin that might be useful to someone else,
please consider submitting it for inclusion
in the official `esc-plugins` directory.
