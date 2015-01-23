# history
import copy

class HistoricalStack(object):
    """
    Manages the stack's history over time, as well as a list of the functions
    the user has invoked. Responsible for undoing as well.
    """

    def __init__(self):
        self.undoStack = []
        self.redoStack = []

    def checkpointState(self, ss):
        if self.redoStack:
            self.redoStack = []
        self.undoStack.append(copy.deepcopy(ss))

    def lastCheckpoint(self, ss):
        if self.undoStack:
            undo = self.undoStack.pop()
            self.redoStack.append(ss)
            return undo
        else:
            return None
    def nextCheckpoint(self, ss):
        if self.redoStack:
            redo = self.redoStack.pop()
            self.undoStack.append(ss)
            return redo
        else:
            return None

# make available as a module global
hs = HistoricalStack()
