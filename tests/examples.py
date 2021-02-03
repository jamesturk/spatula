from spatula import Page, Workflow, NullSource


class ExampleListPage(Page):
    source = NullSource()

    def process_page(self):
        yield {"val": "1"}
        yield {"val": "2"}
        yield {"val": "3"}
        yield {"val": "4"}
        yield {"val": "5"}


simple_5 = Workflow(ExampleListPage)
