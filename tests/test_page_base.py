import logging
import pytest
from spatula import Page, MissingSourceError, HandledError, NullSource
from scrapelib import HTTPError, Scraper

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
    pass


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

    class DependencyTestPage(Page):
        source = SOURCE
        dependencies = {"a_dependency": DependencyPage}

    p = DependencyTestPage()
    p._fetch_data(DummyScraper())
    assert p.a_dependency == "dependency fulfilled"


def test_get_source_from_input_called():
    class SimpleInputPage(Page):
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
    class ErrorPage(Page):
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


def test_fetch_data_postprocess():
    class Postprocess(Page):
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


def test_to_items_simple():
    scraper = Scraper()
    page = FirstPage()
    items = list(page._to_items(scraper))
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
