#!/usr/bin/env bash

if [ ! -f "setup.py" ]; then
    echo "Please run this script from the repository root."
    exit 1
fi

. venv/bin/activate
rm -rf dist/
python setup.py sdist bdist_wheel || exit 1
twine upload --repository-url https://test.pypi.org/legacy dist/*