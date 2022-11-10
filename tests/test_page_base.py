import logging
import pytest
from spatula import (
    Page,
    ListPage,
    MissingSourceError,
    HandledError,
    NullSource,
    SkipItem,
    RejectedResponse,
    config,
)
from scrapelib import HTTPError, Scraper
from .examples import ExamplePaginatedPage

SOURCE = "https://example.com"


class Error:
    status_code = 400
    url = "error"
    text = "error response"


class DummyScraper:
    """a functional mock to be used in _fetch_data tests"""

    def request(self, url, **kwargs):
        if url != "error":
            return f"dummy response for {url}"
        else:
            raise HTTPError(Error())


class DummyPage(Page):
    """a mock Page that can be instantiated without a process_page defined"""

    def process_page(self):
        raise NotImplementedError


def test_page_init_and_str():
    INPUT = "input-value"
    assert str(DummyPage()) == "DummyPage()"
    assert str(DummyPage(INPUT)) == f"DummyPage(input={INPUT} )"
    assert str(DummyPage(source="https://example.com")) == f"DummyPage(source={SOURCE})"
    assert (
        str(DummyPage(INPUT, source="https://example.com"))
        == f"DummyPage(input={INPUT} source={SOURCE})"
    )
    assert DummyPage().logger == logging.getLogger("tests.test_page_base.DummyPage")


def test_fetch_data_dependencies():
    class DependencyPage(Page):
        source = SOURCE

        def process_page(self):
            return "dependency fulfilled"

    class DependencyTestPage(DummyPage):
        source = SOURCE
        dependencies = {"a_dependency": DependencyPage}

    p = DependencyTestPage()
    p._fetch_data(DummyScraper())
    assert p.a_dependency == "dependency fulfilled"


def test_get_source_from_input_called():
    class SimpleInputPage(DummyPage):
        def get_source_from_input(self):
            return self.input["use_this_as_source"]

    p = SimpleInputPage({"use_this_as_source": "https://example.com"})
    p._fetch_data(DummyScraper())
    assert p.source.url == SOURCE


def test_fetch_data_get_source_from_input_missing():
    p = DummyPage()
    with pytest.raises(MissingSourceError):
        p._fetch_data(DummyScraper())


def test_fetch_data_sets_response():
    p = DummyPage(source=SOURCE)
    p._fetch_data(DummyScraper())
    assert p.response == f"dummy response for {SOURCE}"


def test_fetch_data_handle_error_response():
    class ErrorPage(DummyPage):
        _error_was_called = False

        def process_error_response(self, exception):
            self._error_was_called = True

        def postprocess_response(self):
            # ensure postprocess isn't called
            raise Exception("should not happen")

    p = ErrorPage(source="error")
    with pytest.raises(HandledError):
        p._fetch_data(DummyScraper())
    assert p._error_was_called


class RetrySource:
    """fake source that returns a response after being called 3 times"""

    called = 0

    def __init__(self, retries):
        self.retries = retries

    def get_response(self, scraper):
        self.called += 1
        if self.called < 3:
            return scraper.request("http://failure")
        else:
            return scraper.request("http://retried")


class RetryPage(DummyPage):
    """retry as long as 'failure' is in response"""

    config.RETRY_WAIT_SECONDS = 0.1

    def accept_response(self, response):
        return "failure" not in response


def test_retry_success():
    config.RETRY_WAIT_SECONDS = 0.1
    p = RetryPage(source=RetrySource(retries=2))
    p._fetch_data(DummyScraper())
    assert p.response == "dummy response for http://retried"


def test_retry_still_fails():
    config.RETRY_WAIT_SECONDS = 0.1
    p = RetryPage(source=RetrySource(retries=1))
    with pytest.raises(RejectedResponse) as e:
        p._fetch_data(DummyScraper())
        assert "2x" in str(e)


def test_fetch_data_postprocess():
    class Postprocess(DummyPage):
        _postprocessed = False

        def postprocess_response(self):
            self._postprocessed = True

    p = Postprocess(source=SOURCE)
    p._fetch_data(DummyScraper())
    assert p._postprocessed


def test_default_processing():
    p = DummyPage()
    with pytest.raises(ArithmeticError):
        p.process_error_response(ArithmeticError())
    with pytest.raises(NotImplementedError):
        p.process_page()


class SecondPage(Page):
    source = NullSource()

    def process_page(self):
        return {**self.input, "second": "appended"}


class FirstPage(Page):
    source = NullSource()

    def process_page(self):
        yield SecondPage({"first": 1})
        yield SecondPage({"first": 2})
        yield SecondPage({"first": 3})


def test_do_scrape_simple():
    page = FirstPage()
    items = list(page.do_scrape())
    assert len(items) == 3
    assert items[0] == {"first": 1, "second": "appended"}
    assert items[1] == {"first": 2, "second": "appended"}
    assert items[2] == {"first": 3, "second": "appended"}


def test_to_items_scout():
    scraper = Scraper()
    page = FirstPage()
    items = list(page._to_items(scraper, scout=True))
    assert len(items) == 3
    assert items[0] == {
        "data": {"first": 1},
        "__next__": "SecondPage source=NullSource",
    }
    assert items[1] == {
        "data": {"first": 2},
        "__next__": "SecondPage source=NullSource",
    }
    assert items[2] == {
        "data": {"first": 3},
        "__next__": "SecondPage source=NullSource",
    }


def test_paginated_page():
    page = ExamplePaginatedPage()
    items = list(page.do_scrape())
    assert len(items) == 6


def test_paginated_list_page():
    page = ExamplePaginatedPage()
    items = list(page.do_scrape())
    assert len(items) == 6


def test_paginated_single_value_page():
    class SingleReturnPaginatedPage(Page):
        source = NullSource()

        def process_page(self):
            return {"dummy": "value"}

        def get_next_source(self):
            # a hack to fake a second identical page
            if isinstance(self.source, NullSource):
                return "https://httpbin.org/get"

    page = SingleReturnPaginatedPage()
    items = list(page.do_scrape())
    assert len(items) == 2


def test_paginated_page_with_error():
    BAD_URL = "https://httpbin.org/status/500"

    class ErrorThenPaginatedPage(Page):
        source = BAD_URL
        error_handled = False

        def process_page(self):
            return {"dummy": "value"}

        def process_error_response(self, exception):
            self.error_handled = True

        def get_next_source(self):
            # a hack to fake a second identical page
            if self.source.url == BAD_URL:
                return "http://example.com"

    page = ErrorThenPaginatedPage()
    items = list(page.do_scrape())
    assert len(items) == 1
    assert page.error_handled


def test_skip_item(caplog):
    class SkipOddPage(ListPage):
        source = NullSource()

        def process_page(self):
            yield from self._process_or_skip_loop([1, 2, 3, 4, 5])

        def process_item(self, item):
            if item % 2:
                raise SkipItem(f"{item} is odd!")
            else:
                return item

    page = SkipOddPage()
    with caplog.at_level(logging.INFO):
        items = list(page.do_scrape())
    assert items == [2, 4]
    # one for the fetch and 3 for the skips
    assert len(caplog.records) == 4


def test_skip_item_on_detail_page(caplog):
    class SkipOddDetail(Page):
        def process_page(self):
            if self.input % 2:
                raise SkipItem(f"{self.input} is odd!")
            else:
                return self.input

    class SkipOddList(ListPage):
        source = NullSource()

        def process_page(self):
            yield from self._process_or_skip_loop([1, 2, 3, 4, 5])

        def process_item(self, item):
            return SkipOddDetail(item, source=NullSource())

    page = SkipOddList()
    with caplog.at_level(logging.INFO):
        items = list(page.do_scrape())
    assert items == [2, 4]
    assert len(caplog.records) == 9  # 6 null fetches, 3 skips
