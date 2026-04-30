esc
===

**esc** (pronounced /esk/) is an Extensible Stack-based Calculator
designed for efficiency and customizability.
What does this mean?

* esc is *stack-based*,
  operating using a `Reverse Polish Notation`_ (RPN)-like syntax.
  Rather than typing ``2 + 2`` and pressing an equals key,
  you enter the two numbers ``2`` and ``2`` onto :ref:`the stack <Stack>`,
  then choose ``+`` to add them.
  This can be slightly awkward at first,
  but it means no parentheses are necessary,
  and for most people it becomes faster and more elegant
  than the standard algebraic method
  with a small amount of practice.
  In addition, it is considerably easier to customize and program.

* esc is *extensible*.
  If you frequently need to
  multiply two numbers together, add five, and then divide the result by pi,
  you can add a function to the calculator to do this specific operation
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

.. _Reverse Polish Notation: https://en.wikipedia.org/wiki/Reverse_Polish_notation


.. toctree::
   :maxdepth: 3
   :caption: Contents

   using-esc/index
   hacking-esc/index


AI use in this documentation
============================

Small portions of this esc documentation have been drafted or updated by Claude Code
(particularly some of the docstrings).
However, the vast majority of it is human-written from the start,
and all of it has been thoroughly reviewed and edited by a human.

The author of esc sees a need to mention this limited amount of LLM use
only because his `personal LLM policy`_
indicates he never publishes any English text written with LLMs without disclosing it.

.. _personal LLM policy: https://sorenbjornstad.com/ai/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
