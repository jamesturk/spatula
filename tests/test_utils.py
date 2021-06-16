import pprint
from dataclasses import dataclass
import pytest
import lxml.html
from spatula.utils import _display

try:
    import attr
except ImportError:
    attr = None


@pytest.mark.parametrize(
    "data",
    [{}, {"a": 1, "b": ["x", "y", "z"]}],
)
def test_display_pretty(data):
    assert _display(data) == pprint.pformat(data)


@pytest.mark.parametrize(
    "element, output",
    [
        ("<b>test</b>", "<b> @ line 1"),
        ("<p id='p1'>test</p>", "<p id='p1'> @ line 1"),
        ("<p class='styled'>test</p>", "<p class='styled'> @ line 1"),
        ("<p id='p2' class='styled'>test</p>", "<p id='p2'> @ line 1"),
        (
            "<p class='styled' data-elem='ignored'>test</p>",
            "<p class='styled'> @ line 1",
        ),
    ],
)
def test_display_element(element, output):
    assert _display(lxml.html.fromstring(element)) == output


@pytest.mark.parametrize(
    "item, output",
    [("some str", "some str"), (True, "True"), (None, "None"), (1234, "1234")],
)
def test_display_simple(item, output):
    assert _display(item) == output


def test_display_pydantic():
    class ToDictDemo:
        # fake a pydantic-looking class without depending upon pydantic for tests
        __fields__ = ["a", "b"]

        def __init__(self, a, b):
            self.a = a
            self.b = b

        def dict(self):
            return {"val1": self.a, "b": self.b}

    d = ToDictDemo("a", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert _display(d) == "{'b': [1, 2, 3, 4, 5, 6, 7, 8, 9], 'val1': 'a'}"


def test_display_dataclass():
    @dataclass
    class DataclassDemo:
        a: str
        b: int

    d = DataclassDemo("word", 42)
    assert _display(d) == "{'a': 'word', 'b': 42}"


@pytest.mark.skipif(attr is None, reason="requires attrs")
def test_display_attr():
    @attr.s
    class AttrDemo:
        a = attr.ib()
        b = attr.ib()

    d = AttrDemo("word", 42)
    assert _display(d) == "{'a': 'word', 'b': 42}"
