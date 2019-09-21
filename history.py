# history
import copy

class HistoricalStack(object):
    """
    Manages the stack's history over time, as well as a list of the functions
    the user has invoked. Responsible for undoing as well.
    """

    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def checkpointState(self, ss):
        if self.redo_stack:
            self.redo_stack = []
        self.undo_stack.append(ss.memento())

    def undo_to_checkpoint(self, ss, checkpoint_index=-1):
        if self.undo_stack:
            restore_memento = self.undo_stack.pop(checkpoint_index)
            self.redo_stack.append(ss.memento())
            ss.restore(restore_memento)
            return True
        else:
            return False

    def redo_to_checkpoint(self, ss, checkpoint_index=-1):
        if self.redo_stack:
            restore_memento = self.redo_stack.pop(checkpoint_index)
            self.undo_stack.append(ss.memento())
            ss.restore(restore_memento)
            return True
        else:
            return False

# make available as a module global
hs = HistoricalStack()
