import dataclasses
import datetime
import functools
import importlib
import json
import logging
import sys
import typing
import uuid
from pathlib import Path
import lxml.html  # type: ignore
import click
from scrapelib import Scraper, SQLiteCache
from .utils import _display, _obj_to_dict, attr_has, attr_fields
from .sources import URL, Source
from .pages import Page


VERSION = "0.8.3"


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
        "--timeout", default=5, help="set HTTP request timeout in seconds (default: 5)"
    )
    @click.option(
        "--verify/--no-verify", default=True, help="control verification of SSL certs"
    )
    @click.option(
        "--retries",
        default=0,
        help="configure how many retries to perform on HTTP request error (default: 0)",
    )
    @click.option(
        "--retry-wait",
        default=10,
        help="configure how many seconds to wait on HTTP request error (default: 10)",
    )
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
        default=-1,
    )
    @click.option(
        "--fastmode",
        help="use a cache to avoid making unnecessary requests",
        is_flag=True,
    )
    def newfunc(
        header: typing.List[str],
        retries: int,
        retry_wait: int,
        rpm: int,
        timeout: int,
        user_agent: str,
        verbosity: int,
        verify: bool,
        fastmode: bool,
        **kwargs: str,
    ) -> None:
        scraper = Scraper(
            requests_per_minute=rpm,
            retry_attempts=retries,
            retry_wait_seconds=retry_wait,
            verify=verify,
        )
        scraper.timeout = timeout
        scraper.user_agent = user_agent
        # only update headers, don't overwrite defaults
        scraper.headers.update(
            {k.strip(): v.strip() for k, v in [h.split(":") for h in header]}
        )
        if fastmode:
            scraper.cache_storage = SQLiteCache("spatula-cache.db")
            scraper.cache_write_only = False

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


def get_page_class(dotted_name: str) -> type:
    mod_name, cls_name = dotted_name.rsplit(".", 1)
    try:
        mod = importlib.import_module(mod_name)
    except ImportError:
        logging.getLogger("spatula").debug("appending current directory to PYTHONPATH")
        sys.path.append(".")
        mod = importlib.import_module(mod_name)
    Cls = getattr(mod, cls_name)
    return Cls


def get_page(dotted_name: str, source: typing.Optional[str]) -> Page:
    Cls = get_page_class(dotted_name)
    if isinstance(Cls, Page):
        if source:
            Cls.source = URL(source)
        return Cls
    else:
        return Cls(source=source)


def get_new_filename(obj: typing.Any) -> str:
    if hasattr(obj, "get_filename"):
        return obj.get_filename()
    else:
        return str(uuid.uuid4())


def save_object(obj: typing.Any, output_path: Path) -> None:
    filename = output_path / (get_new_filename(obj) + ".json")
    data = _obj_to_dict(obj)
    with open(filename, "w") as f:
        json.dump(data, f)


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

    if hasattr(Cls, "example_input"):
        example = getattr(Cls, "example_input")
        for k, v in fake_input.items():
            if isinstance(example, dict):
                example[k] = v
            else:
                setattr(example, k, v)
        return example

    input_type = getattr(Cls, "input_type", None)
    if input_type:
        click.secho(f"{Cls.__name__} expects input ({input_type.__name__}): ")
        if dataclasses.is_dataclass(input_type):
            fields = dataclasses.fields(input_type)
        elif attr_has(input_type):
            # ignore type rules here since dataclasses/attr do not share a base
            # but fields will have a name no matter what
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
    source: typing.Optional[str],
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

    Example:

    ``` console
    $ spatula test path.to.ClassName --source https://example.com
    ```

    This will run the scraper defined at `path.to.ClassName` against the provided URL.
    """
    Cls = get_page_class(class_name)
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


@cli.command()
@click.argument("initial_page_name")
@click.option(
    "-o", "--output-dir", default=None, help="override default output directory."
)
@click.option("-s", "--source", help="Provide (or override) source URL")
@scraper_params
def scrape(
    initial_page_name: str,
    output_dir: str,
    source: typing.Optional[str],
    scraper: Scraper,
) -> None:
    """
    Run full scrape, and output data to disk.
    """
    initial_page = get_page(initial_page_name, source)
    if not output_dir:
        dirn = 1
        today = datetime.date.today().strftime("%Y-%m-%d")
        while True:
            try:
                output_path = Path(f"_scrapes/{today}/{dirn:03d}")
                output_path.mkdir(parents=True)
                break
            except FileExistsError:
                dirn += 1
    else:
        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True)
        except FileExistsError:
            if len(list(output_path.iterdir())):
                click.secho(f"{output_dir} exists and is not empty", fg="red")
                sys.exit(1)
    count = 0
    for item in initial_page._to_items(scraper):
        save_object(item, output_path)
        count += 1
    click.secho(f"success: wrote {count} objects to {output_path}", fg="green")


@cli.command()
@click.argument("initial_page_name")
@click.option("-s", "--source", help="Provide (or override) source URL")
@click.option(
    "-o",
    "--output-file",
    default="scout.json",
    help="override default output file [default: scout.json].",
)
@scraper_params
def scout(
    initial_page_name: str,
    output_file: str,
    source: typing.Optional[str],
    scraper: Scraper,
) -> None:
    """
    Run first step of scrape & output data to a JSON file.

    This command is intended to be used to detect at a first approximation whether
    or not a full scrape might need to be run. If the first layer detects any changes
    it is safe to say that the full run will as well.

    This will work in the common case where a new subpage is added or removed.
    Of course in more advanced cases this depends upon the first page being scraped
    (typically a ListPage derivative) surfacing enough information (perhaps a
    last_updated date) to know whether any of the other pages have been scraped.
    """
    initial_page = get_page(initial_page_name, source)
    items = list(initial_page._to_items(scraper, scout=True))
    with open(output_file, "w") as f:
        json.dump(items, f, indent=2)
    click.secho(f"success: wrote {len(items)} records to {output_file}", fg="green")


if __name__ == "__main__":  # pragma: no cover
    cli()
