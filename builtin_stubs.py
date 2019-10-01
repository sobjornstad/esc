"""
builtin_stubs.py - stub classes for built-in functions
"""

from menus import BuiltinFunction


class StoreRegister(BuiltinFunction):
    """
    Store the bottommost value on the stack into a register. Registers
    store values under a single-letter name until you need them again.
    """
    key = ">"
    description = "store bos to reg"

    def simulated_result(self, ss, registry):
        if ss.bos is not None:
            return (f"The value {ss.bos}",
                    f"would be stored to a register of your choice.",)
        else:
            return ("An error would occur. (You must have at least",
                    "one item on the stack to store.)")


class RetrieveRegister(BuiltinFunction):
    """
    Retrieve the value of a register you've previously stored to and add it
    to the bottom of the stack. Registers store values under a single-letter
    name until you need them again.
    """
    key = "<"
    description = "get bos from reg"

    def simulated_result(self, ss, registry):
        if len(registry) > 0:  # pylint: disable=len-as-condition
            return ("A register of your choice would have its value",
                    "retrieved and added to the bottom of the stack.")
        else:
            return ("You wouldn't be able to do anything useful. (You ",
                    "must first store a value to a register.)")


class DeleteRegister(BuiltinFunction):
    """
    Remove an existing register from your registers list and destroy its value.
    """
    key = "X"
    description = "delete register"

    def simulated_result(self, ss, registry):
        if len(registry) > 0:  # pylint: disable=len-as-condition
            return ("A register of your choice would be deleted.",)
        else:
            return ("You wouldn't be able to do anything useful.",
                    "(You don't have any registers to delete.)")


class Undo(BuiltinFunction):
    """
    Undo the last change made to your stack. Registers are unaffected. (This
    is a feature, not a bug: a common esc workflow is to reach an answer,
    then realize you need to go back and do something else with those same
    numbers. Registers allow you to hold onto your answer while you do so.)
    """
    key = "u"
    description = "undo"

    def simulated_result(self, ss, registry):
        # Unfortunately, it's hard to imagine getting the necessary information
        # here to update dynamically on whether it's possible.
        return ("The last change made to your stack (if any)",
                "would be undone.",)


class Redo(BuiltinFunction):
    """
    Undo your last undo.
    """
    key = "\x12"  # ^R
    description = "redo"

    def simulated_result(self, ss, registry):
        # Unfortunately, it's hard to imagine getting the necessary information
        # here to update dynamically on whether it's possible.
        return ("Your last undo would be undone (if you just",
                "undid something).",)


class Quit(BuiltinFunction):
    """
    Quit esc. If you're in a menu, this option changes to "cancel" and gets
    you out of the menu instead.
    """
    key = "q"
    description = "quit"

    def simulated_result(self, ss, registry):
        return ("esc would quit.",)
