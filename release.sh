#!/bin/sh
set -e
./run_tests.sh
poetry run bump2version src/spatula/cli.py pyproject.toml docs/conf.py docs/cli.rst --current-version $1 --new-version $2 --commit --tag
poetry publish --build
