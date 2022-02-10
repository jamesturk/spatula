import datetime
import json
from pathlib import Path
from click.testing import CliRunner
from spatula.cli import cli


def test_shell_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["shell", "https://httpbin.org/get"])
    assert result.exit_code == 0
    assert "url: https://httpbin.org/get" in result.output
    assert "resp: " in result.output
    assert "root: " in result.output


def test_scrape_command_basic():
    runner = CliRunner()

    today = datetime.date.today().strftime("%Y-%m-%d")

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["scrape", "tests.examples.ExampleListPage"])
        assert result.exit_code == 0
        assert f"success: wrote 5 objects to _scrapes/{today}/001" in result.output

        # run again, ensure the directory increments
        result = runner.invoke(cli, ["scrape", "tests.examples.ExampleListPage"])
        assert result.exit_code == 0
        assert f"success: wrote 5 objects to _scrapes/{today}/002" in result.output


def test_scrape_command_module():
    runner = CliRunner()

    today = datetime.date.today().strftime("%Y-%m-%d")

    # scrapes 10 items because it runs both test ListPages
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["scrape", "tests.examples"])
        assert result.exit_code == 0
        assert f"success: wrote 10 objects to _scrapes/{today}/001" in result.output


def test_scrape_command_output_dir_flag():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["scrape", "tests.examples.ExampleListPage", "-o", "mydir"]
        )
        assert result.exit_code == 0
        assert "success: wrote 5 objects to mydir" in result.output

        result = runner.invoke(
            cli, ["scrape", "tests.examples.ExampleListPage", "-o", "mydir"]
        )
        assert result.exit_code == 1
        assert "mydir exists and is not empty" in result.output


def test_scrape_command_source_flag():
    runner = CliRunner()
    today = datetime.date.today().strftime("%Y-%m-%d")

    with runner.isolated_filesystem():
        # tests source override
        result = runner.invoke(
            cli,
            [
                "scrape",
                "tests.examples.ExamplePage",
                "--source",
                "https://httpbin.org/get",
            ],
        )
        assert result.exit_code == 0

        assert f"success: wrote 1 objects to _scrapes/{today}/001" in result.output
        files = list(Path(f"_scrapes/{today}/001").glob("*"))
        with open(files[0]) as f:
            assert "https://httpbin.org" in f.read()


def test_scout_command_basic():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["scout", "tests.examples.ExampleListPage"])
        assert result.exit_code == 0
        assert "success: wrote 5 records to scout.json" in result.output

        with open("scout.json") as f:
            data = json.load(f)
            assert len(data) == 5
            assert data[0] == {"data": {"val": "1"}, "__next__": None}


def test_scout_command_subpages():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["scout", "tests.examples.ExampleListPageSubpages"])
        assert result.exit_code == 0
        assert "success: wrote 5 records to scout.json" in result.output

        with open("scout.json") as f:
            data = json.load(f)
            assert len(data) == 5
            assert data[0] == {
                "data": {"val": "1"},
                "__next__": "Subpage source=NullSource",
            }


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
        "paginating for ExamplePaginatedPage source=https://httpbin.org"
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
        "pagination disabled: would paginate for ExamplePaginatedPage source=https://httpbin.org/get"
        in result.output
    )
    # make sure the 6th item is present and numbered correctly
    assert len(result.output.splitlines()) == 4
    assert "6: " not in result.output


def test_test_command_subpages():
    runner = CliRunner()

    result = runner.invoke(cli, ["test", "tests.examples.ExampleListPageSubpages"])
    assert result.exit_code == 0
    assert (
        "would continue with Subpage(input={'val': '5'} source=NullSource)"
        in result.output
    )


def test_test_command_input():
    runner = CliRunner()

    result = runner.invoke(cli, ["test", "tests.examples.SimpleInputPage"])
    assert result.exit_code == 0
    assert "{'name': '~name', 'number': '~number'}" in result.output


def test_test_command_input_data_flag():
    runner = CliRunner()

    result = runner.invoke(
        cli, ["test", "tests.examples.SimpleInputPage", "-d", "number=11"]
    )
    assert result.exit_code == 0
    assert "{'name': '~name', 'number': '11'}" in result.output


def test_test_command_input_interactive_flag():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["test", "tests.examples.SimpleInputPage", "--interactive"],
        input="James\n99\n",
    )
    assert result.exit_code == 0
    assert "{'name': 'James', 'number': '99'}" in result.output


def test_test_command_input_with_example():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["test", "tests.examples.ExampleInputPage"],
    )
    assert result.exit_code == 0
    assert "{'name': 'Tony', 'number': 65}" in result.output
