# Contributing

## Issues

Bug reports, questions, or feature requests can be submitted as [GitHub issues](https://github.com/jamesturk/spatula/issues).

## Developing Locally

0. Before starting, you'll need [poetry](https://python-poetry.org/docs/#installation) installed.
  [pre-commit](https://pre-commit.com/#install) is also recommended.

0. Fork *spatula* and check out your fork:
  ``` console
  $ git clone git@github.com:<your username>/spatula.git
  ```

0. Install pre-commit hooks
  ```
  $ pre-commit install
  ```
  This will make sure that the linters run before each commit, saving you time.

0. Install *spatula* and its development dependencies locally:
  ```
  $ cd spatula
  $ poetry install
  ```
  From here, you can use `poetry run inv` to run several useful maintenance commands.

### Running Tests

`poetry run inv test` will run all tests and write coverage information to `htmlcov/index.html`

### Linting & Type Checking

`poetry run inv lint` will run ruff and black to lint the code style.

`poetry run inv mypy` will run the mypy type checker.

### Building Docs

`poetry run inv docs` will build the docs and watch for changes.
