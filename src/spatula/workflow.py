import os
import json
import uuid
import typing
import scrapelib
from .pages import Page, HandledError


def page_to_items(scraper, page):
    # fetch data for a page, and then call the process_page entrypoint
    try:
        page._fetch_data(scraper)
    except HandledError:
        return
    result = page.process_page()

    # if we got back a generator, we need to process each result
    if isinstance(result, typing.Generator):
        # each item yielded might be a Page or an end-result
        for item in result:
            if isinstance(item, Page):
                yield from page_to_items(scraper, item)
            else:
                yield item

        # after handling a list, check for pagination
        next_source = page.get_next_source()
        if next_source:
            # instantiate the same class with same input, but increment the source
            yield from page_to_items(
                scraper, type(page)(page.input, source=next_source)
            )
    elif isinstance(result, Page):
        # single Page result, recurse deeper
        yield from page_to_items(scraper, result)
    else:
        # end-result, just return as-is
        yield result


class Workflow:
    """
    Define a complete workflow by which items can be scraped and saved to disk.
    """

    def __init__(self, initial_page, *, scraper: scrapelib.Scraper = None):
        if isinstance(initial_page, type):
            self.initial_page = initial_page()
        else:
            self.initial_page = initial_page
        if not scraper:
            self.scraper = scrapelib.Scraper()

    def get_new_filename(self, obj):
        return str(uuid.uuid4())

    def save_object(self, obj, output_dir):
        filename = os.path.join(output_dir, self.get_new_filename(obj))
        if isinstance(obj, dict):
            dd = obj
        else:
            dd = obj.to_dict()
        with open(filename, "w") as f:
            json.dump(dd, f)

    def execute(self, output_dir: str = None) -> None:
        count = 0
        for item in page_to_items(self.scraper, self.initial_page):
            self.save_object(item, output_dir=output_dir)
            count += 1
        return count
