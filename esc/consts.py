"""
consts.py - constant values used across esc
"""

VERSION = "1.0.0-rc1"
PROGRAM_NAME = f"esc {VERSION}"
TESTING = False  # set to True by the test framework
STACKDEPTH = 12
PRECISION = 12
STACKWIDTH = 21  # needs room for sci notation and labels on top of precision

REQUIRED_TERM_WIDTH = 80
REQUIRED_TERM_HEIGHT = 24

QUIT_CHARACTER = 'q'
UNDO_CHARACTER = 'u'
REDO_CHARACTER = '^R'
CONSTANT_MENU_CHARACTER = 'i'
STORE_REG_CHARACTER = '>'
RETRIEVE_REG_CHARACTER = '<'
DELETE_REG_CHARACTER = 'X'
