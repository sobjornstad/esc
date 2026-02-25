"""
consts.py - constant values used across esc
"""

VERSION = "1.0.1"
PROGRAM_NAME = f"esc {VERSION}"
TESTING = False  # set to True by the test framework
STACK_CAPACITY = 12
STACKDEPTH = STACK_CAPACITY  # deprecated alias for plugins
PRECISION = 12
STACKWIDTH = 21  # needs room for sci notation and labels on top of precision

REQUIRED_TERM_WIDTH = 60   # minimum terminal width
REQUIRED_TERM_HEIGHT = 16  # minimum terminal height

QUIT_CHARACTER = 'q'
UNDO_CHARACTER = 'u'
REDO_CHARACTER = '^R'
CONSTANT_MENU_CHARACTER = 'i'
STORE_REG_CHARACTER = '>'
RETRIEVE_REG_CHARACTER = '<'
DELETE_REG_CHARACTER = 'X'
