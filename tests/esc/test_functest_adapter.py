"""
This test file runs all of the tests provided by functions included in the esc
distribution during unit testing, using esc's built-in testing functionality.
This ensures that we don't have to start esc to find errors in them; either
starting esc or running the unit tests will catch issues.
"""

# pylint: disable=invalid-name, wrong-import-order, unused-import

import importlib
from pathlib import Path
import os

from esc.commands import main_menu

# Import built-in functions and official plugins, registering them on the menu.
from esc import functions

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
pluginspath = (script_dir / '..' / '..' / 'esc-plugins').resolve()
for child in sorted(pluginspath.iterdir()):
    if child.is_file() and child.name.endswith('.py'):
        mod_name = child.name.rsplit('.', 1)[0]
        importlib.import_module(mod_name)


def test_functions():
    "All of our built-in functions work."
    main_menu.test()
