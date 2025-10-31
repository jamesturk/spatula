test:
    uv run pytest

lint:
    uv run ruff check

preview:
    uv run mkdocs serve

publish-pypi:
    rm dist/*
    uv build
    uv publish

publish-docs:
    uv run mkdocs build
    netlify deploy --prod -s careful-docs -d site
