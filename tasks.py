from invoke import task


@task
def docs(c, clean=False):
    if clean:
        c.run("rm -rf docs/_build", pty=True)
    c.run("poetry run sphinx-build docs/ docs/_build/html", pty=True)


@task
def test(c, args=""):
    c.run("poetry run pytest --cov=src/ --cov-report html " + args, pty=True)


@task
def mypy(c):
    c.run("poetry run mypy src/", pty=True)


@task(test, mypy)
def testall(c):
    pass


@task(testall)
def release(c, old, new):
    c.run(
        "poetry run bump2version src/spatula/cli.py pyproject.toml docs/conf.py docs/cli.rst"
        "--current-version {old} --new-version {new} --commit --tag",
        pty=True,
    )
    # c.run("git push", pty=True)
    # c.run("git push --tags", pty=True)
    c.run("poetry publish --build", pty=True)
