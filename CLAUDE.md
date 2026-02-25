# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

esc is an extensible stack-based RPN (Reverse Polish Notation) calculator with a curses terminal UI. It runs on Python 3.10+ with no runtime dependencies beyond the standard library (plus `windows-curses` on Windows). Published on PyPI as `esc-calc`.

## Development Setup

```bash
uv sync --group dev --group test --group docs
uv run esc  # launch the calculator
```

## Commands

- **Run tests:** `uv run pytest` (configured in pyproject.toml with `--doctest-modules --cov=esc`)
- **Run a single test file:** `uv run pytest tests/esc/test_stackitem.py`
- **Run a single test:** `uv run pytest tests/esc/test_stackitem.py::test_stackitem_decimal`
- **Lint:** `uv run pylint esc/` (config in pyproject.toml; 88-char line limit)
- **Format:** `uv run yapf` (config in .style.yapf; PEP 8 base, 88-char columns)
- **Build docs:** `uv run sphinx-build -b html docs docs/_build` (Sphinx with RTD theme)

## Architecture

### Entry Point and Main Loop
`esc/__main__.py` — `curses_wrapper()` initializes curses and calls `user_loop()`, which processes keyboard input in a loop. Input is routed through `try_add_to_number()` (digit entry with decimal/scientific notation) and `try_special()` (Enter, Backspace, Undo/Redo, registers) before falling through to `menu.execute()`.

### Stack and Data Layer
`esc/stack.py` — `StackItem` wraps individual values with paired string and `Decimal` representations. `StackState` manages the stack (max depth 12), supports transaction-based mutations with memento snapshots for undo/redo. All arithmetic uses `Decimal` with 12 significant figures.

### Command System (Composite Pattern)
`esc/commands.py` — `EscCommand` is the base class. `Menu` is a composite container; `Operation` wraps a function with metadata (key binding, push count, log format). `Constant` defines named values. The `@Operation` and `@Constant` decorators are the primary API for defining calculator functions.

### Built-in Functions
`esc/functions.py` — All built-in math operations, defined using `@Operation` decorators and organized into menus. Operations specify how many items they pop/push and can include inline self-tests via `.ensure(before=[...], after=[...])`.

### UI Layer
`esc/display.py` — `EscScreen` singleton manages curses windows (StackWindow, CommandWindow, RegisterWindow, StatusWindow, HistoryWindow). Minimum terminal size: 80x24.

`esc/status.py` — `StatusState` tracks the calculator's modal state (Ready, Insert, Menu, Expecting Register/Help).

### Supporting Modules
- `esc/history.py` — Undo/redo via memento pattern on StackState
- `esc/registers.py` — Named single-letter register storage
- `esc/modes.py` — Configurable calculator states (e.g., degrees/radians) via `@Mode` decorator
- `esc/function_loader.py` — Loads user plugins from `~/.esc/plugins/` or `$XDG_CONFIG_HOME/esc/plugins/`
- `esc/oops.py` — Exception hierarchy: `EscError` → `ProgrammingError`, `FunctionExecutionError`, `InsufficientItemsError`, `NotInMenuError`, `RollbackTransaction`
- `esc/functest.py` — Adapter running `.ensure()` self-tests as pytest cases
- `esc/consts.py` — Version and configuration constants

### Stack Terminology
"bos" = bottom of stack (top-most visible item), "sos" = second on stack. Operation function parameters are named accordingly.

## Code Style

- Formatter: yapf (`.style.yapf`), linter: pylint (`pyproject.toml`)
- 88-character line limit
- Single double-quote docstrings for one-liners: `"Close the connection."`
- Doctest-friendly: pytest runs `--doctest-modules`
