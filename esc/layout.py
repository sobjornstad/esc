"""
layout.py - compute window positions and sizes for the esc interface

This module contains a pure-function layout algorithm with no curses
dependency, making it easy to unit-test.
"""

from dataclasses import dataclass

from .consts import STACKWIDTH

# Minimum terminal dimensions for esc to be usable.
MIN_TERM_WIDTH = 60
MIN_TERM_HEIGHT = 16

# Fixed column widths.
STACK_COL_WIDTH = STACKWIDTH + 3  # 24 — border + padding around STACKWIDTH
COMMANDS_COL_WIDTH = 24


@dataclass
class WindowSpec:  # pylint: disable=invalid-name
    "Position and size for a single curses window."
    x: int
    y: int
    width: int
    height: int


@dataclass
class LayoutSpec:
    "Computed layout for every window in the esc interface."
    status: WindowSpec
    stack: WindowSpec
    history: WindowSpec
    commands: WindowSpec
    registers: WindowSpec | None  # None when terminal is too short


UNIT_STACK_COL_WIDTH = STACK_COL_WIDTH + 15  # 39 — wider for unit display


def compute_layout(term_height: int, term_width: int,
                   units_active: bool = False) -> LayoutSpec:
    """
    Compute the layout for all esc windows given the terminal size.

    The layout follows these rules:

    * **Status bar** — 1 row, full width, at the top.
    * **Stack** — fixed width (24, or 39 with units active), gets all
      remaining height after registers.  Minimum 8 content lines
      (11 rows with border/heading).
    * **Commands** — fixed width (24), anchored to the right edge, full
      remaining height.
    * **History** — fills the space between Stack and Commands columns,
      same height as Stack.
    * **Registers** — preferred 5 rows (3 content + 2 border), compressed
      or hidden when the terminal is short.

    >>> layout = compute_layout(24, 80)
    >>> layout.status
    WindowSpec(x=0, y=0, width=80, height=1)
    >>> layout.stack
    WindowSpec(x=0, y=1, width=24, height=18)
    >>> layout.history
    WindowSpec(x=24, y=1, width=32, height=18)
    >>> layout.commands
    WindowSpec(x=56, y=1, width=24, height=23)
    >>> layout.registers
    WindowSpec(x=0, y=19, width=56, height=5)

    >>> small = compute_layout(16, 60)
    >>> small.stack
    WindowSpec(x=0, y=1, width=24, height=11)
    >>> small.history
    WindowSpec(x=24, y=1, width=12, height=11)
    >>> small.commands
    WindowSpec(x=36, y=1, width=24, height=15)
    >>> small.registers
    WindowSpec(x=0, y=12, width=36, height=4)
    """
    # Total available rows below the status bar.
    main_rows = term_height - 1  # 1 row for status

    # Column widths — wider stack when units are active.
    stack_col_width = UNIT_STACK_COL_WIDTH if units_active else STACK_COL_WIDTH
    history_width = term_width - stack_col_width - COMMANDS_COL_WIDTH
    left_width = stack_col_width + history_width  # stack + history span

    # Stack/history get all remaining rows after registers.
    # Registers prefer 5 rows (3 content + 2 border) but compress when short.
    preferred_registers_height = 5  # 3 content + 2 border
    min_stack_height = 11           # 8 content + 2 border + 1 heading

    stack_height = main_rows - preferred_registers_height
    if stack_height < min_stack_height:
        # Compress registers to give stack priority.
        stack_height = min(min_stack_height, main_rows)

    # Registers get whatever is left below the stack/history.
    registers_rows = main_rows - stack_height
    registers_visible = registers_rows >= 3  # need 1 content + 2 border

    status_spec = WindowSpec(x=0, y=0, width=term_width, height=1)
    stack_spec = WindowSpec(x=0, y=1,
                            width=stack_col_width, height=stack_height)
    history_spec = WindowSpec(x=stack_col_width, y=1,
                              width=history_width, height=stack_height)
    commands_spec = WindowSpec(x=left_width, y=1,
                               width=COMMANDS_COL_WIDTH, height=main_rows)

    if registers_visible:
        registers_spec = WindowSpec(
            x=0,
            y=1 + stack_height,
            width=left_width,
            height=registers_rows,
        )
    else:
        registers_spec = None

    return LayoutSpec(
        status=status_spec,
        stack=stack_spec,
        history=history_spec,
        commands=commands_spec,
        registers=registers_spec,
    )
