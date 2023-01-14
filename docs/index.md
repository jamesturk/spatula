# Overview

*spatula* is a modern Python library for writing maintainable web scrapers.

Source: [https://github.com/jamesturk/spatula](https://github.com/jamesturk/spatula)

Documentation: [https://jamesturk.github.io/spatula/](https://jamesturk.github.io/spatula/)

Issues: [https://github.com/jamesturk/spatula/issues](https://github.com/jamesturk/spatula/issues)

[![PyPI badge](https://badge.fury.io/py/spatula.svg)](https://badge.fury.io/py/spatula)
[![Test badge](https://github.com/jamesturk/spatula/workflows/Test%20&%20Lint/badge.svg)](https://github.com/jamesturk/spatula/actions?query=workflow%3A%22Test+%26+Lint%22)

## Features

- **Page-oriented design**: Encourages writing understandable & maintainable scrapers.
- **Not Just HTML**: Provides built in [handlers for common data formats](reference.md#pages) including CSV, JSON, XML, PDF, and Excel.  Or write your own.
- **Fast HTML parsing**: Uses `lxml.html` for fast, consistent, and reliable parsing of HTML.
- **Flexible Data Model Support**: Compatible with `dataclasses`, `attrs`, `pydantic`, or bring your own data model classes for storing & validating your scraped data.
- **CLI Tools**: Offers several [CLI utilities](cli.md) that can help streamline development & testing cycle.
- **Fully Typed**: Makes full use of Python 3 type annotations.

## Installation

*spatula* is on [PyPI](https://pypi.org/project/spatula/), and can be installed via any standard package management tool:

    poetry add spatula

or:

    pip install spatula

## Example

An example of a fairly simple two-page scrape, read [A First Scraper](scraper-basics.md) for a walkthrough of how it was built.

``` python
from spatula import HtmlPage, HtmlListPage, CSS, XPath, SelectorError


class EmployeeList(HtmlListPage):
    # by providing this here, it can be omitted on the command line
    # useful in cases where the scraper is only meant for one page
    source = "https://scrapple.fly.dev/staff"

    # each row represents an employee
    selector = CSS("#employees tbody tr")

    def process_item(self, item):
        # this function is called for each <tr> we get from the selector
        # we know there are 4 <tds>
        first, last, position, details = item.getchildren()
        return EmployeeDetail(
            dict(
                first=first.text,
                last=last.text,
                position=position.text,
            ),
            source=XPath("./a/@href").match_one(details),
        )

    def get_next_source(self):
        try:
            return XPath("//a[contains(text(), 'Next')]/@href").match_one(self.root)
        except SelectorError:
            pass


class EmployeeDetail(HtmlPage):
    def process_page(self):
        status = CSS("#status").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return dict(
            status=status.text,
            hired=hired.text,
            # self.input is the data passed in from the prior scrape
            **self.input,
        )

    def process_error_response(self, exc):
        self.logger.warning(exc)
```
