import datetime
from click.testing import CliRunner
from spatula.cli import cli


def test_shell_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["shell", "https://example.com"])
    assert result.exit_code == 0
    assert "url: https://example.com" in result.output
    assert "resp: " in result.output
    assert "root: " in result.output


def test_scrape_command_basic():
    runner = CliRunner()

    today = datetime.date.today().strftime("%Y-%m-%d")

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["scrape", "tests.examples.simple_5"])
        assert result.exit_code == 0
        assert f"success: wrote 5 objects to _scrapes/{today}/001" in result.output

        # run again, ensure the directory increments
        result = runner.invoke(cli, ["scrape", "tests.examples.simple_5"])
        assert result.exit_code == 0
        assert f"success: wrote 5 objects to _scrapes/{today}/002" in result.output


def test_scrape_command_output_dir_flag():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["scrape", "tests.examples.simple_5", "-o", "mydir"]
        )
        assert result.exit_code == 0
        assert "success: wrote 5 objects to mydir" in result.output

        result = runner.invoke(
            cli, ["scrape", "tests.examples.simple_5", "-o", "mydir"]
        )
        assert result.exit_code == 1
        assert "mydir exists and is not empty" in result.output


def test_test_command_basic():
    runner = CliRunner()

    # tests list output
    result = runner.invoke(cli, ["test", "tests.examples.ExampleListPage"])
    assert result.exit_code == 0
    assert "1: {'val': '1'}" in result.output
    assert "5: {'val': '5'}" in result.output


def test_test_command_example_source():
    runner = CliRunner()

    # tests example source and single element output
    result = runner.invoke(cli, ["test", "tests.examples.ExamplePage"])
    assert result.exit_code == 0
    assert "{'source': 'NullSource'}" in result.output


def test_test_command_source_flag():
    runner = CliRunner()

    # tests example source and single element output
    result = runner.invoke(
        cli, ["test", "tests.examples.ExamplePage", "--source", "https://example.com"]
    )
    assert result.exit_code == 0
    assert "{'source': 'https://example.com'" in result.output


def test_test_command_paginated():
    runner = CliRunner()

    result = runner.invoke(cli, ["test", "tests.examples.ExamplePaginatedPage"])
    assert result.exit_code == 0
    assert (
        "paginating for ExamplePaginatedPage source=https://example.com"
        in result.output
    )
    # make sure the 6th item is present and numbered correctly
    assert "6: " in result.output


def test_test_command_no_pagination():
    runner = CliRunner()

    result = runner.invoke(
        cli, ["test", "tests.examples.ExamplePaginatedPage", "--no-pagination"]
    )
    assert result.exit_code == 0
    assert (
        "pagination disabled: would paginate for ExamplePaginatedPage source=https://example.com"
        in result.output
    )
    # make sure the 6th item is present and numbered correctly
    assert len(result.output.splitlines()) == 4
    assert "6: " not in result.output


# TODO: --data --interactive
