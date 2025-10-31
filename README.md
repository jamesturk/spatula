# Overview

*spatula* is a modern Python library for writing maintainable web scrapers.

**Please note, the official repository has changed to Codeberg; GitHub will only be used as a mirror.**

Source: [https://codeberg.org/jpt/spatula/](https://codeberg.org/jpt/spatula/)

Documentation: <https://spatula.jpt.sh>

Issues: [https://codeberg.org/jpt/spatula/issues](https://codeberg.org/jpt/spatula/issues)

[![PyPI badge](https://badge.fury.io/py/spatula.svg)](https://badge.fury.io/py/spatula)

## Features

- **Page-oriented design**: Encourages writing understandable & maintainable scrapers.
- **Not Just HTML**: Provides built in [handlers for common data formats](https://jamesturk.github.io/spatula/reference/#pages) including CSV, JSON, XML, PDF, and Excel.  Or write your own.
- **Fast HTML parsing**: Uses `lxml.html` for fast, consistent, and reliable parsing of HTML.
- **Flexible Data Model Support**: Compatible with `dataclasses`, `attrs`, `pydantic`, or bring your own data model classes for storing & validating your scraped data.
- **CLI Tools**: Offers several [CLI utilities](https://jamesturk.github.io/spatula/cli/) that can help streamline development & testing cycle.
- **Fully Typed**: Makes full use of Python 3 type annotations.
