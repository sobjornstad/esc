========================
Terminology and Notation
========================

Throughout the rest of this documentation,
we will rely on some simple terminology and notation:

* In esc's interface, the stack window shows numbers from top to bottom.
  To avoid wasting large amounts of space in the documentation,
  we often describe the stack in terms of a Python list,
  with the leftmost element showing at the top,
  so a stack containing the numbers 1, 2, 3, and 4 from top to bottom
  would be described as ``[1, 2, 3, 4]``.

* Certain elements on the :ref:`stack <Stack>`
  need to be discussed frequently
  and have shorthand names in the documentation, interface, and code:

    * **bos** (Bottom of Stack) --
      the item listed at the bottom of the :guilabel:`Stack` window,
      ``4`` in the example above
    * **sos** (Second on Stack) --
      the item listed second from the bottom of the :guilabel:`Stack` window,
      ``3`` in the example above
    * **tos** (Top of Stack)
      -- the item listed at the top of the :guilabel:`Stack` window,
      ``1`` in the example above
