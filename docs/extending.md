extending.md – documentation for extending and customizing esc

This document is a brief introduction to Python programming as needed to add
functions to your calculator, as well as a description of how to use the
interface esc provides. After spending perhaps half an hour working through this
tutorial, you should be able to add your own custom calculation functions to
esc.


Getting Your Feet Wet: Adding a Constant
========================================

Let’s start with something really easy: adding a constant. esc defines pi and e
by default, but that leaves out a lot of other useful and friendly constants.
For this exercise, pick your favorite one. I’ll use *c*, the speed of light in a
vacuum, as an example.

Constants, like all other extensible features in esc, are handled in the file
`functions.py`. Go ahead and open it up in your text editor of choice and look
for the CONSTANTS section. (If you’ve never used a text editor before, look
around for one provided in your operating system or do a Google search. The only
caution I have on this front is that you should not use the Windows default text
editor, Notepad: it is not able to handle all text files correctly, and may
break esc completely. But if you’re using this program on Windows, you are using
Cygwin, and you probably know how to use a text editor, so I digress.) you can
probably figure out how to add a constant just from looking at the ones that are
already there:

    fm.registerConstant(math.pi, 'p', 'pi')
    fm.registerConstant(math.e, 'e', 'e')

Since this is an introduction, though, we’ll take a closer look at these lines
so that we can really understand what’s going on. In programming, we call
`registerConstant` a *function* (in this case, it’s technically a *method*, but
you can safely ignore that if you’re not a programmer) and the things in the
parentheses are the *arguments* to the function; there can be several arguments,
separated by commas. `fm` identifies this function as belonging to the Function
Manager, which is a piece of code that keeps track of all the operations and
constants that you want to have available in esc. So when you want to add a new
function to the calculator, you need to address the request to the Function
Manager, which allows you to communicate with it using a number of predefined
functions like `registerConstant`.

So `registerConstant` has three arguments; in the first predefined line, they
are `math.pi`, `p`, and `pi`. If you fire up esc in another window and look in
the constants window, you’ll see that `p` is the key you press to select pi, and
`pi` is the description of what this constant is (pi – go figure). To see how
this works, try changing the description: just change the contents of the quotes
(currently `pi`) to something else (say, `Mmm! Yummy!`), then save the file,
restart esc, and open the menu again.

So to summarize, the arguments are:

* the constant that you want to push onto the stack when this constant is
  selected
* the letter that you want to use to select it from the menu
* the description that you want to appear next to the letter

In both of the predefined examples, I used a constant from Python’s `math`
library, but you can also just write a number there. If you wish, you can use
scientific notation, written in the same way as inside esc.

So to add the speed of light, I would add the line:

    fm.registerConstant(3.0e9, 'c', 'c - speed of light')

Go ahead and try your own. When adding content to this file or making
significant edits of existing content, beware that Python is extremely picky
about indentation, or the space (or lack thereof) that comes before the first
text character in each line. If you change the indentation of a line to
something incorrect, you may prevent esc from starting. For purposes of editing
your functions file, you will be fine if you follow two simple rules:

* Unless you know that a line is *supposed* to be indented, it isn’t.
* Don’t go around changing lines that you don’t understand.

When you’re done with the edits, save the file, restart esc, and try using the
constant. If you get an error, either when starting the program or when trying
to insert the constant, take a close look at the line you added: Python gets
very angry very quickly if you do something as seemingly insignificant as
leaving out a comma, pairing a double quote and a single quote, or forgetting a closing parenthesis.


Writing Functions
=================

Now that we’ve added a constant, let’s try adding a new operation. For the sake
of example, we’ll make a very simple operation, sometimes called the *increment*
operation. It simply adds one to the last item on the stack.

All operations in esc pop a certain number of items off the stack, then push a
certain number of items back onto the stack. So in our case, we will pop one
item off the stack (which will be the bottom item), add one to it, and then push
it back onto the stack.

There are two steps to this process. First, we need to *write a function* that,
when given a number, will add one to it. Second, we need to *register* the
function with the Function Manager, telling it what we want to call it, where it
should go in the menus, and how many items we want to pop and push.

We talked about functions a little bit in relation to the `registerConstant()`
function. But what exactly *is* a function? Functions in Python can be used in a
great number of different ways and productively thought of in just as many, but
for the purposes of this tutorial I’ll give it a simple definition: A function
is a box with two holes in it. You put values into the top of the box, and some
other value or values come out the output hole. Our job in writing the function
we need for this operation is simply to define what goes on inside the box.

Before we figure out what goes on inside the box, we need to know what is going
to be dropped into the top of our box; it would be no good to design the innards
of our box thinking that we would be getting a marble only to later be told that
we were actually going to be getting a spoon. We also need to know what we’re
expected to put out the other end of our box; if we push the wrong thing out,
then our box could cause the rest of esc to crash.

The rules are quite simple, and they are identical for all functions that you
add to esc:

* The function will be passed one argument, usually called *s*, which is a list
  of values. These are not just any values, of course, but rather the values you
  requested, a certain number of values from the bottom of the stack. The value
  that was at the bottom of the stack (bos) comes first, then (if you
  requested it) sos, and so on.
* The function is asked to return one value, which will either be a list of
  values (if it is supposed to push multiple values onto the stack) or a single
  number (if it is only supposed to push one value onto the stack).
  Specifically, that single number should be a *floating-point* number; since
  the values we are getting in are floating-point numbers and a floating-point
  number operated with any other number is also a floating-point number, this is
  not a distinction we normally need to concern ourselves with.

Here’s a very simple function that meets these requirements, called
`replaceWithPiApproximation`:

    def replaceWithPiApproximation(s):
        return 3.14

When we drop `s` (the function’s argument) into the top of the box, `3.14`
comes out the other end (the *return value*). In the case of this function, we
can in fact drop any `s` we care to try into the top of the box, and it will
have no influence whatsoever on the return value. It’s like the box drops your
`s` into a little trash can inside it and then pulls a pi approximation from
another receptacle and shoots it out the other end.

Here’s another function:

    def doNothingToOneValue(s):
        return s[0]

As the name suggests, we do absolutely nothing to this value: we dropped `s` in
the top and we just moved it along a little track and pushed it out the other
end. However, there is an important proviso in this name as well, and that is
“to one value.” If `s` contained two or three values, we would only be releasing
the first one from the box and holding onto the others. Here’s a version for two
values:

    def doNothingToTwoValues(s):
        return s[0], s[1]

As you can see, if we want to return a list of values, we can simply specify
both of them after the return statement, separated by a comma. As it happens, we
could accomplish the same thing as both of these functions – or for any
arbitrary number of values in the list `s` – by merely writing `return s`, but
the point of this was to show how you can select individual values from the list
provided. Note that the first value is item **0** in the list; this has its
roots in the way that the computer handles memory, but if you prefer to think
it’s just because computer scientists like to be different, you’d probably also
be right there.

You have everything you need to write the increment function. Before you read
further and examine this function closely, take a look at the above functions
and see if you can figure out how you would write the function to add one to a
single value.

<hr>

Here it is:

    def increment(s):
        return s[0] + 1

If you didn’t get it, it was probably because you weren’t sure how to add 1. All
of the normal arithmetic operations are written exactly the same way you would
write them algebraically anywhere else, and parentheses work as you would expect
as well.

Note that the first line of the function is not indented, but the second line
*is*. It doesn’t matter how far it is indented, but if the function uses
multiple lines (we haven’t seen this yet, but you can take several actions
within the same function), they all need to be indented by the same amount. A
common convention is four spaces of indentation.

Registering a Function
======================

So now we have our `increment` function: we’ve built the box, and now we need to
hand it over to the Function Manager so that it can put elements from our stack
into the box and capture the output. In esc, this is called *registering* the
function.

You do this with the function `fm.registerFunction()`, which has six arguments:

* the function you want to register
* the number of arguments you want to pop into the list `s` and have dropped in the box
* the number of arguments you want to push back to the stack (most commonly,
  this will be 1)
* the key you want to use to activate your operation
* the description to put next to it
* the menu you want to put the operation on

The last two arguments can be left out if you wish; if you leave the menu out,
the function will end up on the main menu, and if you leave the description out,
it will be listed at the top without a description, like the arithmetic operations.

For “the function you want to register”, we just use the same name that we wrote
after `def`, the Python keyword for creating and naming a function. So in our
case, we would write `increment` there. I’ll put it on the main menu using the
access key `n`, so the call comes to:

    fm.registerFunction(increment, 1, 1, 'n', 'increment bos')

Notice that some of the arguments go in quotation marks and some do not. There’s
a simple rule for this: things which are numbers (*1*) or are names defined within
the program (our function name, *increment*) do not go in quotation marks, while
text which is destined for the screen does.

It’s a good idea to add a comment describing what your function is for; in our
case, it’s probably pretty self-evident, but just for good measure, I’ll add
one. Any line which begins with `#` is a comment: everything on that line is
completely ignored by the computer. Our increment code thus becomes:

    # increment operator: add one to bos
    def increment(s):
        return s[0] + 1
    fm.registerFunction(increment, 1, 1, 'n', 'increment bos')

Add that text at the end of your file, save it, restart esc, and you should have
a new “increment” option at the bottom of your main menu that will add one to
the bottommost item on the stack.


Using Variables
===============

Now let’s try something a bit more complicated. Let’s say that you frequently
work with cylinders, and you often need to know the surface area and the volume
of a cylinder of given dimensions. As a geometry refresher (don’t worry, I had
to look up the surface area one myself), the relevant equations are as follows:

    SA = 2(pi)rh + 2(pi)r^2
    V = (pi) * r^2 * h

Our box is going to be much more complicated this time, but it can still be
distilled to the same essential elements. Take a moment to think about what the
input and output are going to be before you go on (you don’t need to worry about
the order – just list the quantities that need to go in and come out).

<hr>

There are two items that need to be in `s` when we drop it into the box: the
cylinder’s radius and its height. We then want to spit two values out: the
surface area and the volume.

This function *could* be written on one line, but it will be quite confusing
that way, so we’re going to write it on several lines. To do this, we need to
introduce the concept of a *variable*. Variables are often one of the more
complicated parts of a programming language, but for our purposes in Python
they’re actually extremely simple: you can just think of it as a name to which
you’ve assigned a value. For instance, we could write:

    four = 4
    two = 2
    myFavoriteNumber = 24

We would then have three variables, named `four`, `two`, and `myFavoriteNumber`,
with the appropriate values assigned to them. We could then use them in future
lines of code, like:

    sum = four + two + myFavoriteNumber

...which would come to 30 if you looked at the result or returned it as the
result of a function.

Two things to be aware of before you start using variables:

* When you use a variable inside a function, it doesn’t exist outside the
  function. This means you can reuse the same variable name within several
  different functions if you like, and they won’t interfere with each other. For
  this application, there’s no logical reason why you would *want* them to be
  the same, so that isn’t a problem either.
* Variable names can never contain spaces. (People often use the camelCase
  capitalization convention to point out the word boundaries, or you can
  use_underscores_instead.) They can contain letters, numbers, and underscores,
  but cannot start with a number to avoid confusion with actual numbers. There
  are a few other things you can’t call your variables (like *def* or *and* or
  *return*) because they already have a meaning, but you’re unlikely to run into
  these cases even if you don’t know the list. If you’re getting unexpected
  errors, you might try adding a number or underscore somewhere in your variable
  names, which will guarantee this is not the problem.

We now have everything we need to write the function. Before we try writing any
code, we need to keep track of what goes in and what comes out. In this case,
since we have two inputs and two outputs, we can decide what order they go in.
It doesn’t matter what it is, as long as it’s convenient for you to use, but you
do need to be consistent if you want to get the right answers. Let’s agree that
we will push the radius onto the stack first, then the height, and then we will
run the cylinder operation. When we have finished, we will push the surface area
onto the stack first, then the volume, so the volume will end up at bos and the
surface area at sos.

When we have multiple inputs or outputs, we need to be *very* careful about what
order the arguments are going to be in, because it can get surprisingly
confusing. The convention used in esc is that *element 0 of the list always
corresponds to bos*. This is true whether you are pushing or popping: element 0
of the list will always be the former bos or the future bos. This makes good
sense when you’re popping, because the element that gets popped first (the
bottom of the stack) naturally ends up in the first position. It makes less
sense when you’re pushing, because you have to place the item you want at the
bottom of the stack *first* in the list, even though it’s going to be pushed
*last*. If you hold on tightly to the fact that element 0 of the list is always
bos, you’ll be okay.

Here’s the code:

    def cylinderSAandV(s):
        height = s[0]
        radius = s[1]
        SA = (2 * math.pi * radius * height) + (2 * math.pi * (radius ** 2))
        V = math.pi * (radius ** 2) * height
        return V, SA

There are a couple of worthwhile things to note about this:

* The operator for exponentiation in Python is `**`, not `^`. If you don’t
  remember this and try to use `^`, you will get the wrong answer, because `^`
  *also* means something, and it has nothing whatsoever to do with
  exponentiation. I’ve been there.
* I began by creating the variables “height” and “radius”. I would not have had
  to do this; I could have equivalently written `s[0]` wherever I wrote `height`
  and `s[1]` wherever I wrote `radius`. But doing it this way means that the
  formula is much easier to read (and it’s thus less likely that I make a
  mistake in it). Additionally, if I later realize that I got the order of the
  arguments wrong and `height` should have been `s[1]` and vice versa, I can fix
  the problem by simply changing it there. Indeed, I could pull the SA and V
  lines out of this function and plunk them into any other function (with
  different arguments!) and they would be right at home there, just so long as I
  set `height` and `radius` first.
* I used parentheses in a number of places where they were not strictly
  necessary. Python observes the order of operations you’re used to from algebra
  (albeit with some complications for constructions that algebra does not have),
  but again, it’s easier to read and less likely that you make a mistake, and
  there’s no tax on parentheses.
* The first item we place in the return statement will be pushed first – just
  like the first statement we get in `s` was popped first.

Now we need to register the function. This works exactly the same way as it did
with our increment function – the only difference is that we have a different
number of items to push and pop.

    fm.registerFunction(cylinderSAandV, 2, 2, '(', 'cylinder SA & V')

Plug it into your `functions.py` and try it out! Don’t forget that you need to
register the function *after* you create it in the file, not before. I used the
left parenthesis as a character because every significant letter in “cylinder”
is taken already in the default installation, and the character looks a little
bit like half a cylinder. You might ordinarily put this on a menu, perhaps a
menu called “geometry.”

Of course, after you’ve written a function, if the correct answer is not obvious
(like for our increment function), you should try several times with different
numbers, calculating both manually and with the function, to ensure that it does
the math correctly. If you end up failing a test, building a misshapen table,
losing a game, or crashing a rocket because your untested function did the math
wrong, you have no one to blame but yourself.

Now try a function or two of your own. Armed with these examples, you have a
good start. If you run into trouble, try shooting me an email (visit
http://sorenbjornstad.com for contact info): if I have some spare time, I’m
always happy to help with my software.

Using Menus
===========

Compared to adding operations, adding menus to put them on is very simple. We
use our old friend the FunctionManager again. The function `registerMenu` takes
only two arguments, the letter to use to access the menu from the main screen
and the description of the menu:

    fm.registerMenu('m', 'an example menu')

Then to add something to the menu:
    fm.registerFunction(blah blah blah, 'description', 'm')

The important thing is that after the fifth argument to `registerFunction`, the
description, you add an extra argument, with the letter of the menu you want to
use.

If you screw up when changing menus and try to add a command using a letter that
is already used by another operation on that menu, or try to add to a menu that
doesn’t exist, you will get an `AssertionError` on restarting esc, which will
explain what the problem is and tell you which line the offending registration
is on.

That’s all there is to it!


Removing Existing Functions and Menus
=====================================

esc comes with a variety of predefined functions. But maybe you never need to
add numbers (hey, I won’t judge). Or maybe you never use logarithms. Rather than
have to put up with the functions you don’t use being on your calculator,
preventing you from using those letters for your own functions and taking up
space on your command list, you can remove them.

If you’ve added functions and menus, you can remove functions and menus. After
learning how to add them, you should easily be able to recognize the syntax used
by the predefined additions. When you find the section you don’t need anymore,
you can *comment it out* – that is, in front of every line of code belonging to
it, place the comment character `#`. (You could also just delete it, but if you
deleted the code for addition and then later needed to add some numbers, you
would be stuck subtracting a negative number every time, whereas if you comment
it out you can just uncomment it again later.)

Say I didn’t want the code for addition. So I would find the addition line:

    fm.registerFunction(lambda s: s[1] + s[0], 2, 1, '+')

And I would change it to:

    #fm.registerFunction(lambda s: s[1] + s[0], 2, 1, '+')

If I didn’t want the logarithms code, I would find the `LOGARITHMS` section of
the file and comment out the registerMenu line as well as all of the
registerFunction ones. (Just removing the menu will not work: esc will get upset
at you if you try to register a function on a menu that doesn’t exist.)

Let’s say you used exactly one function from the logarithms menu, log x (the
first one in the file). Then you could comment out the other four lines, then
remove the optional menu argument (which, by default, is `'l'`) from the
registerFunction arguments of the `log x` function, and it would show up on the
main menu while the logarithm menu disappeared. Or you could change it to a
different letter corresponding to a different menu.


Lambda Functions
================

Reading this section is not necessary, but if you like the idea of a cleaner
syntax for simple functions, you can take a look.

For very simple functions, using `def` can be needlessly verbose. For these
cases, Python provides a different function syntax, called `lambda`. Here are
two equivalent functions, a standard version and a lambda version (you should
recognize the function from earlier):

    def increment(s):
        return s[0] + 1

    lambda s: s[0] + 1

The biggest difference with the lambda function is that it does not actually
assign a name to the function. If you just write this on a line by itself, the
function disappears into the aether and does nothing at all, because it’s
impossible to put anything into the box when we don’t know what the box is
called or where we can find it. Therefore, you’ll want to write it *in the
registerFunction statement*, where you write the function name for a standard
function:

    fm.registerFunction(lambda s: s[0] + 1, 1, 1, 'n', 'increment bos')

If you look at the top of `functions.py`, you’ll see that a number of the basic
arithmetic operations and the stack operations are defined with lambda
functions.

It’s possible to write all of the functions we’ve written with lambda functions;
there are some cases in which it is not possible, but for our purposes these
cases rarely come up. For instance, we could theoretically write the cylinder
function thus:

    lambda s: (math.pi*s[1]**2*s[0],2*math.pi*s[1]*s[0]+2*math.pi*s[1]**2)

...but for what are hopefully obvious reasons, it’s generally not a good idea if
the function is very complicated at all. (The parentheses are necessary because
there’s a comma in the middle [to separate the return values], so if you leave
them out, Python doesn’t know where the lambda function ends and the next
argument to registerFunction begins.)


More
====

If you’d like to add more features or you aren’t quite sure how to make a
certain function happen, there’s a very large resource available for you, and
that is the whole world of Python programming resources. The `functions.py` file
is a live Python file which is executed when esc starts, so if you can do it in
Python, you can do it in esc. Python is a Turing-complete programming language,
so if any result is computable given 0-12 input numbers and enough resources,
you can write an esc function to do it.

If you’re comfortable with Python, you can also check out the ref.md file for
some advanced tricks that aren’t mentioned here.
