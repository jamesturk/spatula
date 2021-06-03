#!/bin/sh
poetry run pytest --cov=src/ --cov-report html $1
poetry run mypy src/
