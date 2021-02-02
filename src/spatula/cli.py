import dataclasses
import importlib
import typing
import lxml.html
import click
from scrapelib import Scraper
from .utils import _display
from .core import URL

try:
    from attr import has as attr_has
    from attr import fields as attr_fields
except ImportError:
    attr_has = lambda x: False  # noqa
    attr_fields = lambda x: []  # noqa


VERSION = "0.4.1"


def get_class(dotted_name: str):
    mod_name, cls_name = dotted_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


@click.group()
@click.version_option(version=VERSION)
def cli() -> None:
    pass


@cli.command()
@click.argument("url")
@click.option(
    "-ua",
    "--user-agent",
    default=f"spatula {VERSION}",
    help="override default user-agent",
)
@click.option("-X", "--verb", default="GET", help="set HTTP verb such as POST")
def shell(url: str, user_agent: str, verb: str) -> None:
    """
    Start an interactive Python session to interact with a particular page.
    """
    try:
        from IPython import embed
    except ImportError:
        print("shell command requires IPython")
        return

    # import selectors so they can be used without import
    from .selectors import SelectorError, XPath, SimilarLink, CSS  # noqa

    scraper = Scraper()
    scraper.user_agent = user_agent
    resp = scraper.request(verb, url)
    root = lxml.html.fromstring(resp.content)  # noqa
    click.secho(f"spatula {VERSION} shell", fg="blue")
    click.secho("available selectors: CSS, SimilarLink, XPath", fg="blue")
    click.secho("local variables", fg="green")
    click.secho("---------------", fg="green")
    click.secho("url: %s" % url, fg="green")
    click.secho("resp: requests Response instance", fg="green")
    click.secho(f"root: `lxml HTML element` <{root.tag}>", fg="green")
    embed()


def _get_fake_input(Cls, data, interactive):
    # build fake input from command line data if present
    fake_input = {}
    for item in data:
        k, v = item.split("=", 1)
        fake_input[k] = v

    input_type = getattr(Cls, "input_type", None)

    if hasattr(Cls, "example_input"):
        return getattr(Cls, "example_input")

    if input_type:
        print(f"{Cls.__name__} expects input ({input_type.__name__}): ")
        if dataclasses.is_dataclass(input_type):
            fields = dataclasses.fields(input_type)
        elif attr_has(input_type):
            fields = attr_fields(input_type)
        for field in fields:
            if field.name in fake_input:
                print(f"  {field.name}: {fake_input[field.name]}")
            elif interactive:
                fake_input[field.name] = click.prompt("  " + field.name)
            else:
                dummy_val = f"~{field.name}"
                fake_input[field.name] = dummy_val
                print(f"  {field.name}: {dummy_val}")
        return input_type(**fake_input)
    else:
        return fake_input


@cli.command()
@click.argument("class_name")
@click.option("-i", "--interactive", help="Interactively prompt for missing data.")
@click.option(
    "-d", "--data", multiple=True, help="Provide input data in name=value pairs."
)
@click.option("-s", "--source", help="Provide (or override) source URL")
def test(
    class_name: str, interactive: bool, data: typing.List[str], source: str
) -> None:
    """
    This command allows you to scrape a single page and see the output immediately.  This eases the common cycle of making modifications to a scraper, running a scrape (possibly with long-running but irrelevant portions commented out), and comparing output to what is expected.
    ``test`` can also be useful for debugging existing scrapers, you can see exactly what a single step of the scrape is providing, to help narrow down where erroneous data is coming from.

    Example::

    $ spatula test path.to.ClassName --source https://example.com

    This will run the scraper defined at :py:class:`path.to.ClassName` against the provided URL.
    """
    Cls = get_class(class_name)
    s = Scraper()

    fake_input = _get_fake_input(Cls, data, interactive)

    # special case for passing a single URL source
    if source:
        source = URL(source)
    if not source and hasattr(Cls, "example_source"):
        source = Cls.example_source

    # we need to do the request-response-next-page loop at least once
    once = True
    while source or once:
        once = False
        page = Cls(fake_input, source=source)

        # fetch data after input is handled, since we might need to build the source
        page._fetch_data(s)

        result = page.process_page()

        if isinstance(result, typing.Generator):
            for i, item in enumerate(result):
                print(f"{i}:", _display(item))
        else:
            print(_display(result))

        # will be None in most cases, existing the loop, otherwise we restart
        source = page.get_next_source()
        if source:
            click.secho(
                f"paginating for {page.__class__.__name__}: {source}", fg="blue"
            )


@cli.command()
@click.argument("workflow_name")
@click.option(
    "-o", "--output-dir", default=None, help="override default output directory."
)
def scrape(workflow_name: str, output_dir: str) -> None:
    """
    Run full workflow, and output data to disk.
    """
    workflow = get_class(workflow_name)
    workflow.execute(output_dir=output_dir)


if __name__ == "__main__":
    cli()
