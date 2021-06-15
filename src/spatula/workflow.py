import typing
import scrapelib
from .pages import Page, HandledError
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
