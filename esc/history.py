"""
history.py - manage a history of calculations
"""

class HistoricalStack:
    """
    Manages a history of checkpoints of the stack over time
    and undoes and redoes them.
    """
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def clear(self):
        """
        Clear all history. This is needed after doing testing: we don't want
        the undo history to be cluttered with operations done by automated
        test cases.
        """
        self.undo_stack.clear()
        self.redo_stack.clear()

    def checkpoint_stack(self, ss):
        """
        Create and store a checkpoint for the given StackState.
        """
        if self.redo_stack:
            self.redo_stack = []
        if (not self.undo_stack) or self.undo_stack[-1] != ss.memento():
            self.undo_stack.append(ss.memento())

    def undo(self, ss):
        """
        Mutate the provided StackState to bring it back to the preceding
        checkpoint.

        Returns True if successful, False if no undo states are available.
        """
        if self.undo_stack:
            restore_memento = self.undo_stack.pop()
            self.redo_stack.append(ss.memento())
            ss.restore(restore_memento)
            return True
        else:
            return False

    def redo(self, ss):
        """
        Mutate the provided StackState to bring it forward to the next
        checkpoint in the redo list.

        Returns True if successful, False if no redo states are available.
        """
        if self.redo_stack:
            restore_memento = self.redo_stack.pop()
            self.undo_stack.append(ss.memento())
            ss.restore(restore_memento)
            return True
        else:
            return False


# Make a single HistoricalStack available as a module global.
# pylint: disable=invalid-name
hs = HistoricalStack()
