"Console-script entry point for esc."

import curses

from .__main__ import bootstrap


def main() -> None:
    "Wrap curses and launch esc."
    curses.wrapper(bootstrap)
