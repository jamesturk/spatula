from spatula import Page, Workflow, NullSource


class ExampleListPage(Page):
    # need this here to test that default source is used
    source = NullSource()

    def process_page(self):
        yield {"val": "1"}
        yield {"val": "2"}
        yield {"val": "3"}
        yield {"val": "4"}
        yield {"val": "5"}


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
            return "https://example.com"


class ExamplePage(Page):
    # need this here to test example_sources are picked up
    example_source = NullSource()

    def process_page(self):
        return {"source": str(self.source)}


simple_5 = Workflow(ExampleListPage)
