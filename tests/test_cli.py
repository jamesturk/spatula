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
