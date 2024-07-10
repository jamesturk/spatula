# Command Line Interface

*spatula* provides a command line interface that is useful for iterative development of scrapers.

Once installed within your Python environment, spatula can be invoked on the command line.  E.g.:

``` console
  (scrape-venv) ~/scrape-proj $ spatula --version
  spatula, version 0.9.1
```

Or with poetry:

``` console
  ~/scrape-proj $ poetry run spatula --version
  spatula, version 0.9.1
```

The CLI provides four useful subcommands for different stages of development:

::: mkdocs-click
   :module: spatula.cli
   :command: cli
   :prog_name: spatula
   :depth: 1
   :style: table

