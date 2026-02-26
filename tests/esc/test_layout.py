from esc.layout import compute_layout, MIN_TERM_WIDTH, MIN_TERM_HEIGHT


def test_layout_80x24():
    """At 80x24, stack expands to fill available space."""
    layout = compute_layout(24, 80)

    # Status: row 0, full width
    assert layout.status.x == 0
    assert layout.status.y == 0
    assert layout.status.width == 80
    assert layout.status.height == 1

    # Stack: 24 wide, 18 tall (23 main - 5 registers), starts at (0, 1)
    assert layout.stack.x == 0
    assert layout.stack.y == 1
    assert layout.stack.width == 24
    assert layout.stack.height == 18

    # History: 32 wide, same height as stack, starts at (24, 1)
    assert layout.history.x == 24
    assert layout.history.y == 1
    assert layout.history.width == 32
    assert layout.history.height == 18

    # Commands: 24 wide, full remaining height (23), starts at (56, 1)
    assert layout.commands.x == 56
    assert layout.commands.y == 1
    assert layout.commands.width == 24
    assert layout.commands.height == 23

    # Registers: 56 wide, 5 tall, starts at (0, 19)
    assert layout.registers is not None
    assert layout.registers.x == 0
    assert layout.registers.y == 19
    assert layout.registers.width == 56
    assert layout.registers.height == 5


def test_layout_60x16_minimum():
    """At minimum terminal size, stack gets priority, registers compress."""
    layout = compute_layout(16, 60)

    assert layout.status.width == 60
    assert layout.stack.width == 24
    assert layout.commands.width == 24
    assert layout.history.width == 12  # 60 - 24 - 24
    assert layout.stack.height == layout.history.height

    # Stack gets minimum 11 rows, registers get compressed to 4
    assert layout.stack.height == 11
    assert layout.registers is not None
    assert layout.registers.height == 4

    # Commands span full height
    assert layout.commands.height == 15  # 16 - 1


def test_layout_120x40_large():
    """At a large terminal, stack expands, registers stay at preferred size."""
    layout = compute_layout(40, 120)

    assert layout.history.width == 72  # 120 - 24 - 24
    assert layout.commands.height == 39  # 40 - 1
    assert layout.stack.height == 34   # 39 - 5
    assert layout.registers is not None
    assert layout.registers.height == 5


def test_layout_registers_hidden_when_too_short():
    """When terminal is very short, registers are hidden."""
    # At 14 rows: main=13, stack wants 11, registers get 2 → hidden (< 3).
    layout = compute_layout(14, 80)
    assert layout.registers is None
    assert layout.stack.height == 11

    # At 13 rows: main=12, stack wants 11, registers get 1 → hidden.
    layout = compute_layout(13, 80)
    assert layout.registers is None
    assert layout.stack.height == 11


def test_layout_columns_tile_horizontally():
    """The three columns should tile without gaps or overlap."""
    for width in (60, 80, 100, 120):
        for height in (16, 24, 40):
            layout = compute_layout(height, width)
            # Stack + History + Commands fills the full width
            assert (layout.stack.width + layout.history.width
                    + layout.commands.width) == width
            # No horizontal gaps
            assert layout.history.x == layout.stack.x + layout.stack.width
            assert layout.commands.x == layout.history.x + layout.history.width


def test_layout_no_overlap_vertically():
    """Windows should not overlap vertically."""
    for height in (16, 20, 24, 30, 40):
        layout = compute_layout(height, 80)
        # Stack starts right after status
        assert layout.stack.y == layout.status.y + layout.status.height
        if layout.registers is not None:
            # Registers start right after stack
            assert layout.registers.y == layout.stack.y + layout.stack.height
            # Registers don't extend past terminal
            assert layout.registers.y + layout.registers.height <= height
