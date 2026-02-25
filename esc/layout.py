"""
layout.py - compute window positions and sizes for the esc interface

This module contains a pure-function layout algorithm with no curses
dependency, making it easy to unit-test.
"""

from dataclasses import dataclass

from .consts import STACK_CAPACITY, STACKWIDTH

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


def compute_layout(term_height: int, term_width: int) -> LayoutSpec:
    """
    Compute the layout for all esc windows given the terminal size.

    The layout follows these rules:

    * **Status bar** — 1 row, full width, at the top.
    * **Stack** — fixed width (24), variable height based on available rows.
    * **Commands** — fixed width (24), anchored to the right edge, full
      remaining height.
    * **History** — fills the space between Stack and Commands columns,
      same height as Stack.
    * **Registers** — spans below Stack + History, height is whatever
      rows remain. Hidden if fewer than 3 rows are available.

    At 80x24, the result is identical to the old hardcoded layout.

    >>> layout = compute_layout(24, 80)
    >>> layout.status
    WindowSpec(x=0, y=0, width=80, height=1)
    >>> layout.stack
    WindowSpec(x=0, y=1, width=24, height=15)
    >>> layout.history
    WindowSpec(x=24, y=1, width=32, height=15)
    >>> layout.commands
    WindowSpec(x=56, y=1, width=24, height=23)
    >>> layout.registers
    WindowSpec(x=0, y=16, width=56, height=8)

    >>> small = compute_layout(16, 60)
    >>> small.stack
    WindowSpec(x=0, y=1, width=24, height=12)
    >>> small.history
    WindowSpec(x=24, y=1, width=12, height=12)
    >>> small.commands
    WindowSpec(x=36, y=1, width=24, height=15)
    >>> small.registers
    WindowSpec(x=0, y=13, width=36, height=3)
    """
    # Total available rows below the status bar.
    main_rows = term_height - 1  # 1 row for status

    # Column widths.
    history_width = term_width - STACK_COL_WIDTH - COMMANDS_COL_WIDTH
    left_width = STACK_COL_WIDTH + history_width  # stack + history span

    # Left-column height: enough for STACK_CAPACITY items + border (2 rows),
    # but leave at least 3 rows for registers when possible.
    max_stack_height = STACK_CAPACITY + 3  # border(2) + 1 heading-ish row
    desired_stack_height = min(max_stack_height, main_rows - 3)
    # But never less than 5 (border + a few items).
    stack_height = max(5, min(desired_stack_height, main_rows))

    # Registers get whatever is left below the stack/history.
    registers_rows = main_rows - stack_height
    registers_visible = registers_rows >= 3

    status_spec = WindowSpec(x=0, y=0, width=term_width, height=1)
    stack_spec = WindowSpec(x=0, y=1,
                            width=STACK_COL_WIDTH, height=stack_height)
    history_spec = WindowSpec(x=STACK_COL_WIDTH, y=1,
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
