# Overview

*spatula* is a modern Python library for writing maintainable web scrapers.

Source: [https://github.com/jamesturk/spatula](https://github.com/jamesturk/spatula)

Documentation: [https://jamesturk.github.io/spatula/](https://jamesturk.github.io/spatula/)

Issues: [https://github.com/jamesturk/spatula/issues](https://github.com/jamesturk/spatula/issues)

[![PyPI badge](https://badge.fury.io/py/spatula.svg)](https://badge.fury.io/py/spatula)
[![Test badge](https://github.com/jamesturk/spatula/workflows/Test%20&%20Lint/badge.svg)](https://github.com/jamesturk/spatula/actions?query=workflow%3A%22Test+%26+Lint%22)

## Features

- **Page-oriented design**: Encourages writing understandable & maintainable scrapers.
- **Not Just HTML**: Provides built in [handlers for common data formats](https://jamesturk.github.io/spatula/reference/#pages) including CSV, JSON, XML, PDF, and Excel.  Or write your own.
- **Fast HTML parsing**: Uses `lxml.html` for fast, consistent, and reliable parsing of HTML.
- **Flexible Data Model Support**: Compatible with `dataclasses`, `attrs`, `pydantic`, or bring your own data model classes for storing & validating your scraped data.
- **CLI Tools**: Offers several [CLI utilities](https://jamesturk.github.io/spatula/cli/) that can help streamline development & testing cycle.
- **Fully Typed**: Makes full use of Python 3 type annotations.
