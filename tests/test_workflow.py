from scrapelib import Scraper
from spatula import Page, NullSource
from spatula.workflow import page_to_items


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


def test_page_to_items_simple():
    scraper = Scraper()
    items = list(page_to_items(scraper, FirstPage()))
    assert len(items) == 3
    assert items[0] == {"first": 1, "second": "appended"}
    assert items[1] == {"first": 2, "second": "appended"}
    assert items[2] == {"first": 3, "second": "appended"}


def test_page_to_items_scout():
    scraper = Scraper()
    items = list(page_to_items(scraper, FirstPage(), scout=True))
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
