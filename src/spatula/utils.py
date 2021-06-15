import pprint
import typing
import dataclasses
import scrapelib
from lxml.etree import _Element  # type: ignore
from .pages import Page, HandledError

# utilities for working with optional dependencies
try:
    from attr import has as attr_has
    from attr import fields as attr_fields
    from attr import asdict as attr_asdict
except ImportError:  # pragma: no cover
    attr_has = lambda x: False  # type: ignore # noqa
    attr_fields = lambda x: []  # type: ignore # noqa
    attr_asdict = lambda x: {}  # type: ignore # noqa


def _display_element(obj: _Element) -> str:
    elem_str = f"<{obj.tag} "

    # := if we drop 3.7
    id_str = obj.get("id")
    class_str = obj.get("class")

    if id_str:
        elem_str += f"id='{id_str}'"
    elif class_str:
        elem_str += f"class='{class_str}'"
    else:
        elem_str += " ".join(f"{k}='{v}'" for k, v in obj.attrib.items())

    return f"{elem_str.strip()}> @ line {obj.sourceline}"


def _is_pydantic(obj: typing.Any) -> bool:
    return hasattr(obj, "__fields__") and hasattr(obj, "dict")


def _display(obj: typing.Any) -> str:
    if isinstance(obj, _Element):
        return _display_element(obj)
    else:
        # if there's a dict representation, use that, otherwise str
        try:
            return pprint.pformat(_obj_to_dict(obj))
        except ValueError:
            return str(obj)


def _obj_to_dict(obj: typing.Any) -> typing.Optional[typing.Dict]:
    if obj is None or isinstance(obj, dict):
        return obj
    elif dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    elif attr_has(obj):
        return attr_asdict(obj)
    elif _is_pydantic(obj):
        return obj.dict()
    else:
        raise ValueError(f"invalid type: {obj} ({type(obj)})")


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
