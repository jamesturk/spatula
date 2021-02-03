#!/bin/sh
poetry run pytest --cov=src/ --cov-report html
