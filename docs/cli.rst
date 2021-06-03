Command Line Usage
==================

**spatula** provides a command line interface that is useful for iterative development of scrapers.

Once installed within your Python environment, spatula can be invoked on the command line.  E.g.::

  (scrape-venv) ~/scrape-proj $ spatula --version
  spatula, version 0.6.0

Or with poetry::

  ~/scrape-proj $ poetry run spatula --version
  spatula, version 0.6.0

The CLI provides four useful subcommands for different stages of development:

.. click:: spatula.cli:shell
   :prog: spatula shell
   :nested: full

.. click:: spatula.cli:test
   :prog: spatula test
   :nested: full

.. click:: spatula.cli:scrape
   :prog: spatula scrape
   :nested: full

.. click:: spatula.cli:scout
   :prog: spatula scout
   :nested: full
