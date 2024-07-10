# Changelog

!!! note
spatula 1.0 should be ready in a few months, providing a more stable interface to build upon, until then interfaces may change between releases.

## 0.9.1 - 2024-07-10

- add support for new versions of lxml and Python

## 0.9.0 - 2022-02-10

- add `Page.accept_response` method that can be overriden to trigger custom retry logic
- add preliminary spatula.config for setting/overriding global defaults
  (this feature is not yet considered stable, it likely will be modified before 1.0)

## 0.8.10 - 2022-01-31

- update click dependency

## 0.8.9 - 2021-12-14

- fix for `--rmdir` not recreating directory

## 0.8.8 - 2021-12-09

- add `--rmdir` flag to `spatula scrape`

## 0.8.7 - 2021-11-09

- add support for raising `SkipItem` from a detail page to resume processing
  without yielding data from the page

## 0.8.6 - 2021-10-13

- add `timeout` argument to URL source
- add `--subpages` argument to `spatula test` which runs
  similarly to `spatula scrape` but writes output to the terminal

## 0.8.5 - 2021-08-09

- add `verify` argument to URL source
- improve messaging when using `spatula test`
- add `--dump` flag to `spatula scrape` to control output format

## 0.8.4 - 2021-07-15

- `self.skip` is deprecated in favor of raising `SkipItem`
- add experimental support for module arguments to `scrape` command

## 0.8.3 - 2021-06-23

- fix bug where default headers were cleared by default
- update to scrapelib 2.0.6 which contains a bugfix for a redirect follow bug

## 0.8.2 - 2021-06-22

- fix `spatula --version` to report correct version
- allow `--data` command line flags to override `example_input` values
- add caching of `dependencies`
- fix pagination on non-list pages
- add advanced documentation & anatomy of a scrape

## 0.8.1 - 2021-06-17

- remove undocumented `page_to_items` function
- added `Page.do_scrape` to programmatically get all items from a scrape
- added `--source` parameter to scout & scrape commands

## 0.8.0 - 2021-06-15

- remove undocumented `Workflow`
- allow using `Page` instances (as opposed to just the type) for scout & scrape
- add check for `get_filename` on output classes to override default filename
- improved automatic `pydantic` support
- add --timeout, --no-verify, --retries, --retry-wait options
- add --fastmode option to use local cache
- fix all CLI commands to obey various scraper options

## 0.7.1 - 2021-06-14

- remove undocumented default behavior for `get_source_from_input`
- major documentation overhaul
- fixes for scout scrape when working with raw data returns

## 0.7.0 - 2021-06-04

- add `spatula scout` command
- make error messages a bit more clear
- improvements to documentation
- added more CLI options to control verbosity, user agent, etc.
- if module cannot be found, search current directory

## 0.6.0 - 2021-04-12

- add full typing to library
- small bugfixes

## 0.5.0 - 2021-02-04

- add `ExcelListPage`
- improve `Page.logger` and CLI output
- move to simpler `Workflow` class
- `spatula scrape` can now take the name of a page, will use default
  Workflow
- bugfix: inconsistent name for `process_error_response`

## 0.4.1 - 2021-02-01

- bugfix: dependencies are instantiated from parent page input

## 0.4.0 - 2021-02-01

- restore Python 3.7 compatibility
- add behavior to handle returning additional `Page` subclasses to
  continue scraping
- add default behavior when `Page.input` has a `url` attribute.
- add `PdfPage`
- add `page_to_items` helper
- add `Page.example_input` and `Page.example_source` for test command
- add `Page.logger` for logging
- allow use of `dataclasses` in addition to `attrs` as input objects
- improve output of HTML elements
- bugfix: not specifying a page processor on workflow is no longer an
  error

## 0.3.0 - 2021-01-18

- first documented major release
