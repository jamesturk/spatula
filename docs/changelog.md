# Changelog

!!! note
    spatula 1.0 should be ready by Fall of 2021, providing a more stable interface to build upon, until then interfaces may change between releases.

## WIP

- remove undocumented default behavior for `get_source_from_input`
- major documentation overhaul

## 0.7.0 - 2021-06-04

-   add `spatula scout` command
-   make error messages a bit more clear
-   improvements to documentation
-   added more CLI options to control verbosity, user agent, etc.
-   if module cannot be found, search current directory

## 0.6.0 - 2021-04-12

-   add full typing to library
-   small bugfixes

## 0.5.0 - 2021-02-04

-   add `ExcelListPage`
-   improve `Page.logger` and CLI output
-   move to simpler `Workflow` class
-   `spatula scrape` can now take the name of a page, will use default
    Workflow
-   bugfix: inconsistent name for `process_error_response`

## 0.4.1 - 2021-02-01

-   bugfix: dependencies are instantiated from parent page input

## 0.4.0 - 2021-02-01

-   restore Python 3.7 compatibility
-   add behavior to handle returning additional `Page` subclasses to
    continue scraping
-   add default behavior when `Page.input` has a `url` attribute.
-   add `PdfPage`
-   add `page_to_items` helper
-   add `Page.example_input` and `Page.example_source` for test command
-   add `Page.logger` for logging
-   allow use of `dataclasses` in addition to `attrs` as input objects
-   improve output of HTML elements
-   bugfix: not specifying a page processor on workflow is no longer an
    error

## 0.3.0 - 2021-01-18

-   first documented major release
-   major refactor, inspired by not directly using code from prior
    versions
