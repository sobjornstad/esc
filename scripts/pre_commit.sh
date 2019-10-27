#!/usr/bin/env bash

if [ ! -f "setup.py" ]; then
    echo "Please run this script from the repository root."
    exit 1
fi

. venv/bin/activate
pytest
exit $?
