import dataclasses
import datetime
import glob
import importlib
import logging
import functools
import os
import sys
import typing
import lxml.html  # type: ignore
import click
from scrapelib import Scraper
from .utils import _display
from .sources import URL, Source
from .workflow import Workflow

try:
    from attr import has as attr_has
    from attr import fields as attr_fields
except ImportError:  # pragma: no cover
    attr_has = lambda x: False  # type: ignore # noqa
    attr_fields = lambda x: []  # type: ignore # noqa


VERSION = "0.6.0"


def scraper_params(func: typing.Callable) -> typing.Callable:
    @functools.wraps(func)
    @click.option(
        "-ua",
        "--user-agent",
        default=f"spatula {VERSION}",
        help="override default user-agent",
    )
    @click.option("--rpm", default=60, help="set requests per minute (default: 60)")
    @click.option(
        "-H",
        "--header",
        help="add a header to all requests. example format: 'Accept: application/json'",
        multiple=True,
    )
    @click.option(
        "-v",
        "--verbosity",
        help="override default verbosity for command (0-3)",
        type=int,
        default=-1,
    )
    def newfunc(
        user_agent: str,
        rpm: int,
        header: typing.List[str],
        verbosity: int,
        **kwargs: str,
    ) -> None:
        scraper = Scraper(requests_per_minute=rpm)
        scraper.user_agent = user_agent
        # double ignore, weird issue on 3.7?
        scraper.headers = {  # type: ignore
            k.strip(): v.strip() for k, v in [h.split(":") for h in header]
        }  # type: ignore

        if verbosity == -1:
            level = logging.INFO if func.__name__ != "test" else logging.DEBUG
        elif verbosity == 0:
            level = logging.ERROR
        elif verbosity == 1:
            level = logging.INFO
        elif verbosity >= 2:
            level = logging.DEBUG

        if verbosity < 3:
            # replace parent library logging
            logging.getLogger("scrapelib").setLevel(logging.ERROR)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.basicConfig(level=level)

        return func(**kwargs, scraper=scraper)

    return newfunc


def get_class(dotted_name: str) -> typing.Union[type, Workflow]:
    mod_name, cls_name = dotted_name.rsplit(".", 1)
    try:
        mod = importlib.import_module(mod_name)
    except ImportError:
        logging.getLogger("spatula").debug("appending current directory to PYTHONPATH")
        sys.path.append(".")
        mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


@click.group()
@click.version_option(version=VERSION)
def cli() -> None:
    pass


@cli.command()
@click.argument("url")
@click.option("-X", "--verb", default="GET", help="set HTTP verb such as POST")
@scraper_params
def shell(url: str, verb: str, scraper: Scraper) -> None:
    """
    Start a session to interact with a particular page.
    """
    try:
        from IPython import embed  # type: ignore
    except ImportError:  # pragma: no cover
        click.secho("shell command requires IPython", fg="red")
        return

    # import selectors so they can be used without import
    from .selectors import SelectorError, XPath, SimilarLink, CSS  # noqa

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


def _get_fake_input(Cls: type, data: typing.List[str], interactive: bool) -> typing.Any:
    # build fake input from command line data if present
    fake_input = {}
    for item in data:
        k, v = item.split("=", 1)
        fake_input[k] = v

    input_type = getattr(Cls, "input_type", None)

    if hasattr(Cls, "example_input"):
        return getattr(Cls, "example_input")

    if input_type:
        click.secho(f"{Cls.__name__} expects input ({input_type.__name__}): ")
        if dataclasses.is_dataclass(input_type):
            fields = dataclasses.fields(input_type)
        elif attr_has(input_type):
            # ignore type rules here since dataclasses/attr do not share a base
            # but fields will have a name no matter what
            # TODO: consider interface?
            fields = attr_fields(input_type)  # type: ignore
        for field in fields:
            if field.name in fake_input:
                click.secho(f"  {field.name}: {fake_input[field.name]}")
            elif interactive:
                fake_input[field.name] = click.prompt("  " + field.name)
            else:
                dummy_val = f"~{field.name}"
                fake_input[field.name] = dummy_val
                click.secho(f"  {field.name}: {dummy_val}")
        return input_type(**fake_input)
    else:
        return fake_input


@cli.command()
@click.argument("class_name")
@click.option(
    "--interactive/--no-interactive",
    default=False,
    help="Interactively prompt for missing data.",
)
@click.option(
    "-d", "--data", multiple=True, help="Provide input data in name=value pairs."
)
@click.option("-s", "--source", help="Provide (or override) source URL")
@click.option(
    "--pagination/--no-pagination",
    default=True,
    help="Determine whether or not pagination should be followed or one page is "
    "enough for testing",
)
@scraper_params
def test(
    class_name: str,
    interactive: bool,
    data: typing.List[str],
    source: str,
    pagination: bool,
    scraper: Scraper,
) -> None:
    """
    Scrape a single page and see output immediately.

    This eases the common cycle of making modifications to a scraper, running a scrape
    (possibly with long-running but irrelevant portions commented out), and comparing
    output to what is expected.

    ``test`` can also be useful for debugging existing scrapers, you can see exactly
    what a single step of the scrape is providing, to help narrow down where
    erroneous data is coming from.

    Example::

    $ spatula test path.to.ClassName --source https://example.com

    This will run the scraper defined at :py:class:`path.to.ClassName` against the
    provided URL.
    """
    # TODO: remove if workflow goes away
    Cls = typing.cast(type, get_class(class_name))
    source_obj: typing.Optional[Source] = None

    fake_input = _get_fake_input(Cls, data, interactive)

    # special case for passing a single URL source as a string
    if source:
        source_obj = URL(source)
    if not source_obj and hasattr(Cls, "example_source"):
        source_obj = Cls.example_source  # type: ignore

    # we need to do the request-response-next-page loop at least once
    once = True
    num_items = 0
    while source_obj or once:
        once = False
        page = Cls(fake_input, source=source_obj)

        # fetch data after input is handled, since we might need to build the source
        page._fetch_data(scraper)

        result = page.process_page()

        if isinstance(result, typing.Generator):
            for item in result:
                # use this count instead of enumerate to handle pagination
                num_items += 1
                click.echo(click.style(f"{num_items}: ", fg="green") + _display(item))
        else:
            click.secho(_display(result))

        # will be None in most cases, existing the loop, otherwise we restart
        source_obj = page.get_next_source()
        if source_obj:
            if pagination:
                click.secho(
                    f"paginating for {page.__class__.__name__} source={source_obj}",
                    fg="blue",
                )
            else:
                click.secho(
                    "pagination disabled: would paginate for "
                    f"{page.__class__.__name__} source={source_obj}",
                    fg="yellow",
                )
                break


def get_workflow(workflow_name: str) -> Workflow:
    workflow_or_page = get_class(workflow_name)
    if isinstance(workflow_or_page, Workflow):
        workflow = workflow_or_page
    else:
        workflow = Workflow(workflow_or_page)
    return workflow


@cli.command()
@click.argument("workflow_name")
@click.option(
    "-o", "--output-dir", default=None, help="override default output directory."
)
@scraper_params
def scrape(workflow_name: str, output_dir: str, scraper: Scraper) -> None:
    """
    Run full workflow, and output data to disk.
    """
    workflow = get_workflow(workflow_name)
    if not output_dir:
        dirn = 1
        today = datetime.date.today().strftime("%Y-%m-%d")
        while True:
            try:
                output_dir = f"_scrapes/{today}/{dirn:03d}"
                os.makedirs(output_dir)
                break
            except FileExistsError:
                dirn += 1
    else:
        try:
            os.makedirs(output_dir)
        except FileExistsError:
            if len(glob.glob(output_dir + "/*")):
                click.secho(f"{output_dir} exists and is not empty", fg="red")
                sys.exit(1)
    count = workflow.execute(output_dir=output_dir)
    click.secho(f"success: wrote {count} objects to {output_dir}", fg="green")


@cli.command()
@click.argument("workflow_name")
@click.option(
    "-o",
    "--output-file",
    default="scout.json",
    help="override default output file [default: scout.json].",
)
@scraper_params
def scout(workflow_name: str, output_file: str, scraper: Scraper) -> None:
    """
    Run first step of workflow & output data to a JSON file.

    This command is intended to be used to detect at a first approximation whether
    or not a full scrape might need to be run. If the first layer detects any changes
    it is safe to say that the full run will as well.

    This will work in the common case where a new subpage is added or removed.
    Of course in more advanced cases this depends upon the first page being scraped
    (typically a ListPage derivative) surfacing enough information (perhaps a
    last_updated date) to know whether any of the other pages have been scraped.
    """
    workflow = get_workflow(workflow_name)
    count = workflow.scout(output_file=output_file)
    click.secho(f"success: wrote {count} records to {output_file}", fg="green")


if __name__ == "__main__":  # pragma: no cover
    cli()
