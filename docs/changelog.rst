Changelog
=========

0.4.0 - 
------------------

* restore Python 3.7 compatibility
* add default behavior when `Page.input` has a `url` attribute.
* add :py:class:`PdfPage`
* add `page_to_items` helper
* add `Page.example_input` and `Page.example_source` for test command
* add `Page.logger` for logging
* add `Workflow.yield_items` method
* allow use of `dataclasses` in addition to `attrs` as input objects
* improve output of HTML elements
* bugfix: not specifying a page processor on workflow is no longer an error


0.3.0 - 2021-01-18
------------------

* first documented major release
* major refactor, inspired by not directly using code from prior versions
