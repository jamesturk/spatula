import io
import csv
import tempfile
import subprocess
import logging
import warnings
import typing
import scrapelib
import lxml.html  # type: ignore
from openpyxl import load_workbook  # type: ignore
from .sources import Source, URL
from .utils import _obj_to_dict


def _to_scout_result(result: typing.Any) -> typing.Dict[str, typing.Any]:
    _next: typing.Optional[str]
    if isinstance(result, Page):
        data = _obj_to_dict(result.input)
        _next = f"{result.__class__.__name__} source={result.source}"
    else:
        data = _obj_to_dict(result)
        _next = None
    return {
        "data": data,
        "__next__": _next,
    }


class SkipItem(Exception):
    """
    To be raised to skip processing of the current item & continue with the next item.

    Example:
    ``` python
    class SomeListPage(HtmlListPage):
        def process_item(self, item):
            if item.name == "Vacant":
                raise SkipItem("vacant")
            # do normal processing here
    ```

    Or, if the skip logic needs to live within a detail Page:
    ``` python
    class SomeDetailPage(HtmlPage):
        def process_page(self):
            if self.input.name == "Vacant":
                raise SkipItem("vacant")
            # do normal processing here
    ```
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class MissingSourceError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class HandledError(Exception):
    def __init__(self, exc: Exception):
        super().__init__(exc)


class Page:
    """
    Base class for all *Page* scrapers, used for scraping information from a single type of page.

    For details on how these methods are called, it may be helpful to read
    [Anatomy of a Scrape](anatomy-of-a-scrape.md).

    **Attributes**

    `source`
    :   Can be set on subclasses of `Page` to define the initial HTTP request
        that the page will handle in its `process_response` method.

        For simple GET requests, `source` can be a string.
        `URL` should be used for more advanced use cases.

    `response`
    :   [`requests.Response`](https://docs.python-requests.org/en/master/api/#requests.Response)
        object available if access is needed to the raw response for any reason.

    `input`
    :   Instance of data being passed upon instantiation of this page.
        Must be of type `input_type`.

    `input_type`
    :   `dataclass`, `attrs` class, or `pydantic` model.
        If set will be used to prompt for and/or validate `self.input`

    `example_input`
    :   Instance of `input_type` to be used when invoking `spatula test`.

    `example_source`
    :   Source to fetch when invoking `spatula test`.

    `dependencies`
    :   Dictionary mapping of names to `Page` objects that will be available before `process_page`.

        For example:
        ``` python

        class EmployeeDetail(HtmlPage):
            dependencies = {"awards": AwardsPage()}
        ```

        Means that before `EmployeeDetail.process_page` is called, it is guaranteed to have the
        output from `AwardsPage` available as `self.awards`.

        See [Specifying Dependencies](advanced-techniques.md#specifying-dependencies) for
        a more detailed explanation.

    **Methods**
    """

    source: typing.Union[None, str, Source] = None
    dependencies: typing.Dict[str, "Page"] = {}
    _cached_dependencies: typing.Dict[str, typing.Any] = {}

    def _fetch_data(self, scraper: scrapelib.Scraper) -> None:
        """
        ensure that the page has all of its data, this is guaranteed to be called
        exactly once before process_page is invoked
        """
        # process dependencies first
        for key, dep in self.dependencies.items():
            use_cache = False
            if isinstance(dep, type):
                dep = dep(self.input)
            else:
                use_cache = True

            if key in self._cached_dependencies:
                setattr(self, key, self._cached_dependencies[key])
            else:
                dep._fetch_data(scraper)
                page_result = dep.process_page()
                setattr(self, key, page_result)
                if use_cache:
                    self._cached_dependencies[key] = page_result

        if not self.source:
            try:
                self.source = self.get_source_from_input()
            except NotImplementedError:
                raise MissingSourceError(
                    f"{self.__class__.__name__} has no source or get_source_from_input"
                )
        if isinstance(self.source, str):
            self.source = URL(self.source)
        # at this point self.source is indeed a Source
        self.logger.info(f"fetching {self.source}")
        try:
            self.response = self.source.get_response(scraper)  # type: ignore
            if getattr(self.response, "fromcache", None):
                self.logger.debug(f"retrieved {self.source} from cache")
        except scrapelib.HTTPError as e:
            self.process_error_response(e)
            raise HandledError(e)
        else:
            self.postprocess_response()

    def _paginate(
        self, scraper: scrapelib.Scraper, scout: bool
    ) -> typing.Iterable[typing.Any]:
        next_source = self.get_next_source()
        if next_source:
            # instantiate the same class with same input, but increment the source
            next_page = type(self)(self.input, source=next_source)
            yield from next_page._to_items(scraper, scout=scout)

    def _to_items(
        self, scraper: scrapelib.Scraper, *, scout: bool = False
    ) -> typing.Iterable[typing.Any]:
        # fetch data for a page, and then call the process_page entrypoint
        try:
            self._fetch_data(scraper)
        except HandledError:
            # ok to proceed, but nothing left to do with this page
            yield from self._paginate(scraper, scout)
            return
        try:
            result = self.process_page()
        except SkipItem as e:
            # a detail page can raise SkipItem, which means no further processing of
            # that detail page (as there is no result)
            self.logger.info(f"SkipItem: {e}")
            return

        # if we got back a generator, we need to process each result
        if isinstance(result, typing.Generator):
            # each item yielded might be a Page or an end-result
            for item in result:
                if scout:
                    yield _to_scout_result(item)
                elif isinstance(item, Page):
                    yield from item._to_items(scraper)
                else:
                    yield item
        elif scout:
            yield _to_scout_result(result)
        elif isinstance(result, Page):
            # single Page result, recurse deeper
            yield from result._to_items(scraper)
        else:
            # end-result, just return as-is
            yield result

        # check for next page
        yield from self._paginate(scraper, scout)

    def __init__(
        self,
        input_val: typing.Any = None,
        *,
        source: typing.Union[None, str, Source] = None,
    ):
        self.input = input_val
        # allow possibility to override default source, useful during dev
        if source:
            self.source = source
        self.logger = logging.getLogger(
            self.__class__.__module__ + "." + self.__class__.__name__
        )

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}("
        if self.input:
            s += f"input={self.input} "
        if self.source:
            s += f"source={self.source}"
        s += ")"
        return s

    def do_scrape(
        self, scraper: typing.Optional[scrapelib.Scraper] = None
    ) -> typing.Iterable[typing.Any]:
        """
        yield results from this page and any subpages

        :param scraper: Optional `scrapelib.Scraper` instance to use for running scrape.
        :returns: Generator yielding results from the scrape.
        """
        if scraper is None:
            scraper = scrapelib.Scraper()
        yield from self._to_items(scraper)

    def get_source_from_input(self) -> typing.Union[None, str, Source]:
        """
        To be overridden.

        Convert `self.input` to a `Source` object such as a `URL`.
        """
        raise NotImplementedError()

    def postprocess_response(self) -> None:
        """
        To be overridden.

        This is called after source.get_response but before self.process_page.
        """
        pass

    def process_error_response(self, exception: Exception) -> None:
        """
        To be overridden.

        This is called after source.get_response if an exception is raised.
        """
        raise exception

    def process_page(self) -> typing.Any:
        """
        To be overridden.

        Return data extracted from this page and this page alone.
        """
        raise NotImplementedError()

    def get_next_source(self) -> typing.Union[None, str, Source]:
        """
        To be overriden for paginated pages.

        Return a URL or valid source to fetch the next page, None if there isn't one.
        """
        return None


class HtmlPage(Page):
    """
    Page that automatically handles parsing and normalizing links in an HTML response.

    **Attributes**

    `root`
    :   [`lxml.etree.Element`](https://lxml.de/api/lxml.etree._Element-class.html)
    object representing the root element (e.g. `<html>`) on the page.

        Can use the normal lxml methods (such as `cssselect` and `getchildren`), or
        use this element as the target of a `Selector` subclass.
    """

    def postprocess_response(self) -> None:
        self.root = lxml.html.fromstring(self.response.content)
        if hasattr(self.source, "url"):
            self.root.make_links_absolute(self.source.url)  # type: ignore


class XmlPage(Page):
    """
    Page that automatically handles parsing a XML response.

    **Attributes**

    `root`
    :   [`lxml.etree.Element`](https://lxml.de/api/lxml.etree._Element-class.html)
    object representing the root XML element on the page.
    """

    def postprocess_response(self) -> None:
        self.root = lxml.etree.fromstring(self.response.content)


class JsonPage(Page):
    """
    Page that automatically handles parsing a JSON response.

    **Attributes**

    `data`
    :   JSON data from response.  (same as `self.response.json()`)
    """

    def postprocess_response(self) -> None:
        self.data = self.response.json()


class PdfPage(Page):  # pragma: no cover
    """
    Page that automatically handles converting a PDF response to text using `pdftotext`.

    **Attributes**

    `preserve_layout`
    :   set to `True` on derived class if you want the conversion function to use pdftotext's
        -layout option to attempt to preserve the layout of text.
        (`False` by default)

    `text`
    :   UTF8 text extracted by pdftotext.
    """

    preserve_layout = False

    def postprocess_response(self) -> None:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(self.response.content)
            temp.flush()
            temp.seek(0)

            if self.preserve_layout:
                command = ["pdftotext", "-layout", temp.name, "-"]
            else:
                command = ["pdftotext", temp.name, "-"]

            try:
                pipe = subprocess.Popen(
                    command, stdout=subprocess.PIPE, close_fds=True
                ).stdout
            except OSError as e:
                raise EnvironmentError(
                    f"error running pdftotext, missing executable? [{e}]"
                )
            if pipe is None:
                raise EnvironmentError("no stdout from pdftotext")
            else:
                data = pipe.read()
                pipe.close()
        self.text = data.decode("utf8")


class ListPage(Page):
    """
    Base class for common pattern of extracting many homogenous items from one page.

    Instead of overriding `process_response`, subclasses should provide a `process_item`.

    **Methods**
    """

    def skip(self, msg: str = "") -> None:  # pragma: no cover
        warnings.warn(
            "self.skip is deprecated and will be removed in 0.9, raise SkipItem instead",
            DeprecationWarning,
        )
        raise SkipItem(msg)

    def _process_or_skip_loop(
        self, iterable: typing.Iterable
    ) -> typing.Iterable[typing.Any]:
        for item in iterable:
            try:
                item = self.process_item(item)
            except SkipItem as e:
                self.logger.info(f"SkipItem: {e}")
                continue
            yield item

    def process_item(self, item: typing.Any) -> typing.Any:
        """
        To be overridden.

        Called once per subitem on page, as defined by the particular subclass being used.

        Should return data extracted from the `item`.

        If [`SkipItem`](#SkipItem) is raised, `process_item` will continue to be called with
        the next item in the stream.
        """
        warnings.warn(f"process_item not overridden on {self.__class__.__name__}")
        return item


class CsvListPage(ListPage):
    """
    Processes each row in a CSV (after the first, assumed to be headers) as an item
    with `process_item`.
    """

    def postprocess_response(self) -> None:
        self.reader = csv.DictReader(io.StringIO(self.response.text))

    def process_page(self) -> typing.Iterable[typing.Any]:
        yield from self._process_or_skip_loop(self.reader)


class ExcelListPage(ListPage):  # pragma: no cover
    """
    Processes each row in an Excel file as an item with `process_item`.
    """

    def postprocess_response(self) -> None:
        workbook = load_workbook(io.BytesIO(self.response.content))
        # TODO: allow selecting this with a class property
        self.worksheet = workbook.active

    def process_page(self) -> typing.Iterable[typing.Any]:
        yield from self._process_or_skip_loop(self.worksheet.values)


class LxmlListPage(ListPage):
    """
    Base class for XML and HTML subclasses below, only difference is which
    parser is used.

    Simplification for pages that get a list of items and process them.

    When overriding the class, instead of providing process_page, one must only provide
    a selector and a process_item function.
    """

    selector = None

    def process_page(self) -> typing.Iterable[typing.Any]:
        if not self.selector:
            raise NotImplementedError("must either provide selector or override scrape")
        items = self.selector.match(self.root)
        yield from self._process_or_skip_loop(items)


class HtmlListPage(LxmlListPage, HtmlPage):
    """
    Selects homogenous items from HTML page using `selector` and passes them to `process_item`.

    **Attributes**

    `selector`
    :   `Selector` subclass which matches list of homogenous elements to process.  (e.g. `CSS("tbody tr")`)
    """

    pass


class XmlListPage(LxmlListPage, XmlPage):
    """
    Selects homogenous items from XML document using `selector` and passes them to `process_item`.

    **Attributes**

    `selector`
    :   `Selector` subclass which matches list of homogenous elements to process.  (e.g. `XPath("//item")`)
    """

    pass


class JsonListPage(ListPage, JsonPage):
    """
    Processes each element in a JSON list as an item with `process_item`.
    """

    def process_page(self) -> typing.Iterable[typing.Any]:
        yield from self._process_or_skip_loop(self.data)
