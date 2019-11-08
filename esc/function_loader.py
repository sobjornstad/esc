"""
function_loader.py - load esc functions from builtins and plugins onto menus
"""

import importlib
import os
from pathlib import Path
import sys

from .oops import ProgrammingError


def _import_user_functions():
    """
    Dynamically import any .py files in the user's esc plugins directory.

    The plugins directory is just inside the esc config directory (which
    presently doesn't contain anything else!) This is the first of ~/.esc or
    $XDG_CONFIG_HOME/share/esc or ~/.config/esc that is found.

    The files are imported with the esc namespace first on the path, so doing
    e.g., 'from esc.commands import main_menu' will work automagically,
    even if esc isn't on the PYTHONPATH.
    """
    xdg_home = os.environ.get('XDG_CONFIG_HOME', str(Path.home() / ".config"))
    possible_dirs = (Path.home() / ".esc" / "plugins",
                     Path(xdg_home) / "esc" / "plugins")
    try:
        config_path = next(i for i in possible_dirs
                           if i.exists() and i.is_dir())
    except StopIteration:
        # no config path, don't import anything
        return

    sys.path.insert(0, str(config_path))
    for child in sorted(config_path.iterdir()):
        try:
            if child.is_file() and child.name.endswith('.py'):
                mod_name = child.name.rsplit('.', 1)[0]
                importlib.import_module(mod_name)
        except Exception as e:
            raise ProgrammingError(
                f"Your custom function file '{str(child)}' could not be loaded. "
                f"Please see the traceback above for details.") from e
    del sys.path[0]


def load_all():
    """
    Load built-in and user functions files. This will execute the
    constructors in the functions files, which will (if these files are
    written correctly) ultimately register the functions onto main_menu. This
    method needs to be called only once at application startup.
    """
    from . import functions  # pylint: disable=unused-import, wrong-import-position
    _import_user_functions()
