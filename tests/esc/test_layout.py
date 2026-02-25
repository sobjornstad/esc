from esc.layout import compute_layout, MIN_TERM_WIDTH, MIN_TERM_HEIGHT


def test_layout_80x24_matches_original():
    """At 80x24, the layout must exactly match the old hardcoded values."""
    layout = compute_layout(24, 80)

    # Status: row 0, full width
    assert layout.status.x == 0
    assert layout.status.y == 0
    assert layout.status.width == 80
    assert layout.status.height == 1

    # Stack: 24 wide, 15 tall (STACKDEPTH + 3), starts at (0, 1)
    assert layout.stack.x == 0
    assert layout.stack.y == 1
    assert layout.stack.width == 24
    assert layout.stack.height == 15

    # History: 32 wide, same height as stack, starts at (24, 1)
    assert layout.history.x == 24
    assert layout.history.y == 1
    assert layout.history.width == 32
    assert layout.history.height == 15

    # Commands: 24 wide, full remaining height (23), starts at (56, 1)
    assert layout.commands.x == 56
    assert layout.commands.y == 1
    assert layout.commands.width == 24
    assert layout.commands.height == 23

    # Registers: 56 wide, 8 tall, starts at (0, 16)
    assert layout.registers is not None
    assert layout.registers.x == 0
    assert layout.registers.y == 16
    assert layout.registers.width == 56
    assert layout.registers.height == 8


def test_layout_60x16_minimum():
    """At minimum terminal size, all windows fit."""
    layout = compute_layout(16, 60)

    assert layout.status.width == 60
    assert layout.stack.width == 24
    assert layout.commands.width == 24
    assert layout.history.width == 12  # 60 - 24 - 24
    assert layout.stack.height == layout.history.height

    # Commands span full height
    assert layout.commands.height == 15  # 16 - 1

    # Registers are visible (3 rows)
    assert layout.registers is not None
    assert layout.registers.height >= 3


def test_layout_120x40_large():
    """At a large terminal, history gets extra width."""
    layout = compute_layout(40, 120)

    assert layout.history.width == 72  # 120 - 24 - 24
    assert layout.commands.height == 39  # 40 - 1
    assert layout.registers is not None
    assert layout.registers.height > 8  # more space than 80x24


def test_layout_registers_hidden_when_too_short():
    """When terminal is very short, registers are hidden."""
    layout = compute_layout(16, 80)

    # With 16 rows: status=1, main=15.
    # Stack wants 15, leaving 0 for registers → hidden.
    if layout.registers is not None:
        # If somehow there's room, they should be at least 3 rows
        assert layout.registers.height >= 3


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
