import io
import csv
import tempfile
import subprocess
import logging
import scrapelib
import lxml.html
from openpyxl import load_workbook
from .sources import URL


class MissingSourceError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class HandledError(Exception):
    def __init__(self, exc):
        super().__init__(exc)


class Page:
    source = None
    dependencies = {}

    def _fetch_data(self, scraper: scrapelib.Scraper) -> None:
        """
        ensure that the page has all of its data, this is guaranteed to be called
        exactly once before process_page is invoked
        """
        # process dependencies first
        for val, dep in self.dependencies.items():
            if isinstance(dep, type):
                dep = dep(self.input)
            dep._fetch_data(scraper)
            setattr(self, val, dep.process_page())

        if not self.source:
            if hasattr(self, "get_source_from_input"):
                self.source = self.get_source_from_input()
            elif hasattr(self.input, "url"):
                self.source = URL(self.input.url)
            else:
                raise MissingSourceError(
                    f"{self.__class__.__name__} has no source or get_source_from_input"
                )
        if isinstance(self.source, str):
            self.source = URL(self.source)
        self.logger.info(f"fetching {self.source}")
        try:
            self.response = self.source.get_response(scraper)
        except scrapelib.HTTPError as e:
            self.process_error_response(e)
            raise HandledError(e)
        else:
            self.postprocess_response()

    def __init__(self, input_val=None, *, source=None):
        self.input = input_val
        # allow possibility to override default source, useful during dev
        if source:
            self.source = source
        self.logger = logging.getLogger(
            self.__class__.__module__ + "." + self.__class__.__name__
        )

    def __str__(self):
        s = f"{self.__class__.__name__}("
        if self.input:
            s += f"input={self.input} "
        if self.source:
            s += f"source={self.source}"
        s += ")"
        return s

    def postprocess_response(self) -> None:
        """
        To be overridden.

        This is called after source.get_response but before self.process_page.
        """
        pass

    def process_error_response(self, exception) -> None:
        """
        To be overridden.

        This is called after source.get_response if an exception is raised.
        """
        raise exception

    def process_page(self):
        """
        To be overridden.

        Return data extracted from this page and this page alone.
        """
        raise NotImplementedError()

    def get_next_source(self):
        """
        To be overriden for paginated pages.

        Return a URL or valid source to fetch the next page, None if there isn't one.
        """
        return None


class HtmlPage(Page):
    """
    self.root: preprocessed lxml.html-parsed HTML element
    """

    def postprocess_response(self) -> None:
        self.root = lxml.html.fromstring(self.response.content)
        if hasattr(self.source, "url"):
            self.root.make_links_absolute(self.source.url)


class XmlPage(Page):
    """
    self.root: preprocessed lxml.etree-parsed XML element
    """

    def postprocess_response(self) -> None:
        self.root = lxml.etree.fromstring(self.response.content)


class JsonPage(Page):
    """
    self.data: preprocessed JSON
    """

    def postprocess_response(self) -> None:
        self.data = self.response.json()


class PdfPage(Page):  # pragma: no cover
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
            data = pipe.read()
            pipe.close()
        self.text = data.decode("utf8")


class ListPage(Page):
    class SkipItem(Exception):
        def __init__(self, msg):
            super().__init__(msg)

    def skip(self, msg: str = "") -> None:
        raise self.SkipItem(msg)

    def _process_or_skip_loop(self, iterable):
        for item in iterable:
            try:
                item = self.process_item(item)
            except self.SkipItem as e:
                self.logger.debug(f"SkipItem: {e}")
                continue
            yield item

    def process_item(self, item):
        return item


class CsvListPage(ListPage):
    def postprocess_response(self) -> None:
        self.reader = csv.DictReader(io.StringIO(self.response.text))

    def process_page(self):
        yield from self._process_or_skip_loop(self.reader)

    def process_item(self, item):
        return item


class ExcelListPage(ListPage):
    def postprocess_response(self) -> None:
        workbook = load_workbook(io.BytesIO(self.response.content))
        # TODO: allow selecting this with a class property
        self.worksheet = workbook.active

    def process_page(self):
        yield from self._process_or_skip_loop(self.worksheet.values)

    def process_item(self, item):
        return item


class LxmlListPage(ListPage):
    """
    Base class for XML and HTML subclasses below, only difference is which
    parser is used.

    Simplification for pages that get a list of items and process them.

    When overriding the class, instead of providing process_page, one must only provide
    a selector and a process_item function.
    """

    selector = None

    def process_page(self):
        if not self.selector:
            raise NotImplementedError("must either provide selector or override scrape")
        items = self.selector.match(self.root)
        yield from self._process_or_skip_loop(items)


class HtmlListPage(LxmlListPage, HtmlPage):
    pass


class XmlListPage(LxmlListPage, XmlPage):
    pass


class JsonListPage(ListPage, JsonPage):
    def process_page(self):
        yield from self._process_or_skip_loop(self.data)
