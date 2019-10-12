========
Notation
========

Throughout the rest of this documentation,
we will rely on some simple notation:

* In esc's interface, the stack window shows numbers from top to bottom.
  To avoid wasting large amounts of space in the documentation,
  we often describe the stack in terms of a Python list,
  with the leftmost element showing at the top,
  so a stack containing the numbers 1, 2, and 3 from top to bottom
  would be described ``[1, 2, 3]``.

* Certain elements on the stack need to be discussed frequently
  and have shorthand names in the documentation and the code:

    * **bos** (Bottom of Stack) --
      the item listed at the bottom of the :guilabel:`Stack` window
    * **sos** (Second on Stack) --
      the item listed second from the bottom of the :guilabel:`Stack` window
    * **tos** (Top of Stack)
      -- the item listed at the top of the :guilabel:`Stack` window
