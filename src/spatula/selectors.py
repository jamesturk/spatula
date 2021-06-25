import re
from typing import Optional, List, Iterator
from lxml.etree import _Element  # type: ignore
from .utils import _display


class SelectorError(ValueError):
    """
    Error raised when a selector's constraint (min_items/max_items, etc.) is not met.
    """

    pass


class Selector:
    """
    Base class implementing **Selector** interface.
    """

    def __init__(
        self,
        *,
        min_items: Optional[int] = 1,
        max_items: Optional[int] = None,
        num_items: Optional[int] = None,
    ):
        self.min_items = min_items
        self.max_items = max_items
        self.num_items = num_items

    def match(
        self,
        element: _Element,
        *,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        num_items: Optional[int] = None,
    ) -> List[_Element]:
        """
        Return all matches of the given selector within `element`.

        If the number of elements matched is outside the prescribed boundaries, a
        `SelectorError` is raised.

        :param element: The element to match within. When used from within a `Page` will
                        usually be `self.root`.
        :param min_items: A minimum number of items to match.
        :param max_items: A maximum number of items to match.
        :param num_items: An exact number of items to match.
        """
        items = list(self.get_items(element))
        num_items = self.num_items if num_items is None else num_items
        max_items = self.max_items if max_items is None else max_items
        min_items = self.min_items if min_items is None else min_items

        if num_items is not None and len(items) != num_items:
            raise SelectorError(
                f"{self} on {_display(element)} got {len(items)} results, "
                f"expected {num_items}"
            )
        if min_items is not None and len(items) < min_items:
            raise SelectorError(
                f"{self} on {_display(element)} got {len(items)} results, "
                f"expected at least {min_items}"
            )
        if max_items is not None and len(items) > max_items:
            raise SelectorError(
                f"{self} on {_display(element)} got {len(items)} results, "
                f"expected at most {max_items}"
            )

        return items

    def match_one(self, element: _Element) -> _Element:
        """
        Return exactly one match.

        :param element: Element to search within.
        """
        return self.match(element, num_items=1)[0]

    def get_items(self, element: _Element) -> Iterator[_Element]:  # pragma: no cover
        raise NotImplementedError()


class XPath(Selector):
    def __init__(
        self,
        xpath: str,
        *,
        min_items: Optional[int] = 1,
        max_items: Optional[int] = None,
        num_items: Optional[int] = None,
    ):
        """
        Utilize [XPath](https://en.wikipedia.org/wiki/XPath#Examples) selectors.

        :param xpath: XPath expression to use.
        :param min_items: A minimum number of items to match.
        :param max_items: A maximum number of items to match.
        :param num_items: An exact number of items to match.
        """
        super().__init__(min_items=min_items, max_items=max_items, num_items=num_items)
        self.xpath = xpath

    def get_items(self, element: _Element) -> Iterator[_Element]:
        yield from element.xpath(self.xpath)

    def __str__(self) -> str:  # pragma: no cover
        return f"XPath({self.xpath})"


class SimilarLink(Selector):
    def __init__(
        self,
        pattern: str,
        *,
        min_items: Optional[int] = 1,
        max_items: Optional[int] = None,
        num_items: Optional[int] = None,
    ):
        """
        Match links that fit a provided pattern.

        :param pattern: Regular expression for link hrefs.
        :param min_items: A minimum number of items to match.
        :param max_items: A maximum number of items to match.
        :param num_items: An exact number of items to match.
        """
        super().__init__(min_items=min_items, max_items=max_items, num_items=num_items)
        self.pattern = re.compile(pattern)

    def get_items(self, element: _Element) -> Iterator[_Element]:
        seen = set()
        for element in element.xpath("//a"):
            href = element.get("href")
            if (
                href
                and href not in seen
                and self.pattern.match(element.get("href", ""))
            ):
                yield element
                seen.add(href)

    def __str__(self) -> str:  # pragma: no cover
        return f"SimilarLink({self.pattern})"


class CSS(Selector):
    def __init__(
        self,
        css_selector: str,
        *,
        min_items: Optional[int] = 1,
        max_items: Optional[int] = None,
        num_items: Optional[int] = None,
    ):
        """
        Utilize CSS-style selectors.

        :param css_selector: CSS selector expression to use.
        :param min_items: A minimum number of items to match.
        :param max_items: A maximum number of items to match.
        :param num_items: An exact number of items to match.
        """
        super().__init__(min_items=min_items, max_items=max_items, num_items=num_items)
        self.css_selector = css_selector

    def get_items(self, element: _Element) -> Iterator[_Element]:
        yield from element.cssselect(self.css_selector)

    def __str__(self) -> str:  # pragma: no cover
        return f"CSS({self.css_selector})"
