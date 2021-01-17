Command Line Usage
==================

**spatula** provides a command line interface that is useful for iterative development of scrapers.

Once installed within your Python environment, spatula can be invoked on the command line.  E.g.::

  (scrape-venv) ~/scrape-proj $ spatula --version
  spatula, version 0.3.0

Or with poetry::

  ~/scrape-proj $ poetry run spatula --version
  spatula, version 0.3.0

The CLI provides three useful subcommands for different stages of development:

shell
-----

TODO

test
----

This command allows you to scrape a single page and see the output immediately.  This eases the common cycle of making modifications to a scraper, running a scrape (possibly with long-running but irrelevant portions commented out), and comparing output to what is expected. 
``test`` can also be useful for debugging existing scrapers, you can see exactly what a single step of the scrape is providing, to help narrow down where erroneous data is coming from.

Example::

$ spatula test path.to.ClassName --source https://example.com

This will run the scraper defined at :py:class:`path.to.ClassName` against the provided URL.

Options:

``-i``, ``--interactive``
  Handle input interactively, prompt for any missing input values.

``-d``, ``--data``
  Provide input data by key name.  (e.g. ``--data name=value`` will set the input field ``name`` to ``value``)

  (this option can be provided multiple times)

``-s``, ``--source``
  Provide (or override) source URL.

scrape
------

TODO
