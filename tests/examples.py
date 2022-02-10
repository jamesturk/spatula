from dataclasses import dataclass
from spatula import Page, NullSource, ListPage


class ExampleListPage(ListPage):
    # need this here to test that default source is used
    source = NullSource()

    def process_page(self):
        yield {"val": "1"}
        yield {"val": "2"}
        yield {"val": "3"}
        yield {"val": "4"}
        yield {"val": "5"}


class Subpage(Page):
    source = NullSource()

    def process_page(self):
        return self.input


class ExampleListPageSubpages(ListPage):
    # need this here to test that default source is used
    source = NullSource()

    def process_page(self):
        yield Subpage({"val": "1"})
        yield Subpage({"val": "2"})
        yield Subpage({"val": "3"})
        yield Subpage({"val": "4"})
        yield Subpage({"val": "5"})


class ExamplePaginatedPage(Page):
    source = NullSource()
    another_page = True

    def process_page(self):
        yield {"val": "a man"}
        yield {"val": "a plan"}
        yield {"val": "panama"}

    def get_next_source(self):
        # a hack to fake a second identical page
        if isinstance(self.source, NullSource):
            return "https://httpbin.org/get"


class ExamplePage(Page):
    # need this here to test example_sources are picked up
    example_source = NullSource()

    def process_page(self):
        return {"source": str(self.source)}


@dataclass
class Input:
    name: str
    number: int


class SimpleInputPage(Page):
    source = NullSource()
    input_type = Input

    def process_page(self):
        return {"name": self.input.name, "number": self.input.number}


class ExampleInputPage(SimpleInputPage):
    example_input = Input("Tony", 65)
