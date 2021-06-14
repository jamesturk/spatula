import os
import json
import uuid
import typing
import dataclasses
import scrapelib
from .pages import Page, HandledError
from .maybe import attr_has, attr_asdict


def _to_dict(obj: typing.Any) -> typing.Optional[typing.Dict]:
    if obj is None or isinstance(obj, dict):
        return obj
    elif dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    elif attr_has(obj):
        return attr_asdict(obj)
    elif hasattr(obj, "to_dict"):
        # TODO: remove this option in favor of above
        return obj.to_dict()  # type: ignore
    else:
        raise ValueError(f"invalid type: {obj} ({type(obj)})")


def _to_scout_result(result: typing.Any) -> typing.Dict[str, typing.Any]:
    if isinstance(result, Page):
        data = _to_dict(result.input)
        _next = f"{result.__class__.__name__} source={result.source}"
    else:
        data = _to_dict(result)
        _next = None
    return {
        "data": data,
        "__next__": _next,
    }


def page_to_items(
    scraper: scrapelib.Scraper, page: Page, *, scout: bool = False
) -> typing.Iterable[typing.Any]:

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
                if scout:
                    yield _to_scout_result(item)
                else:
                    yield from page_to_items(scraper, item)
            else:
                if scout:
                    yield _to_scout_result(item)
                else:
                    yield item

        # after handling a list, check for pagination
        next_source = page.get_next_source()
        if next_source:
            # instantiate the same class with same input, but increment the source
            yield from page_to_items(
                scraper, type(page)(page.input, source=next_source), scout=scout
            )
    elif scout:
        yield _to_scout_result(result)
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

    def __init__(
        self,
        initial_page: typing.Union[type, Page],
        *,
        scraper: scrapelib.Scraper = None,
    ):
        if isinstance(initial_page, type):
            self.initial_page = initial_page()
        else:
            self.initial_page = initial_page
        if not scraper:
            self.scraper = scrapelib.Scraper()

    def get_new_filename(self, obj: typing.Any) -> str:
        return str(uuid.uuid4())

    def save_object(self, obj: typing.Any, output_dir: str) -> None:
        filename = os.path.join(output_dir, self.get_new_filename(obj))
        data = _to_dict(obj)
        with open(filename, "w") as f:
            json.dump(data, f)

    def execute(self, output_dir: str) -> int:
        count = 0
        for item in page_to_items(self.scraper, self.initial_page):
            self.save_object(item, output_dir=output_dir)
            count += 1
        return count

    def scout(self, output_file: str) -> int:
        items = list(page_to_items(self.scraper, self.initial_page, scout=True))
        with open(output_file, "w") as f:
            json.dump(items, f, indent=2)
        return len(items)
