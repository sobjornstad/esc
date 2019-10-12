beginners.md – a brief introduction to RPN as used in esc

I intend to add some exercises and examples to this to help ease people into RPN soon.

Understanding the Stack
=======================

If you’ve previously used an RPN-based calculator or calculator program and are
comfortable with the concept of the stack and how to use it to perform
calculations, you can skip this section if you like.

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
the stack. If you make a typo, you can correct it with Backspace.

You can enter as many numbers as you like this way, at least until the stack
fills up. (In esc, the stack size is based on the number of lines allocated for
the stack on the screen, which is ordinarily 12. Twelve entries should be more
than enough for all but the craziest calculations; many RPN-based HP calculators
only have four, and that is usually enough.)

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

