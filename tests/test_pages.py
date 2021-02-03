import json
from dataclasses import dataclass
from spatula import (
    HtmlPage,
    XmlPage,
    JsonPage,
    CsvListPage,
    HtmlListPage,
    XmlListPage,
    JsonListPage,
    XPath,
    URL,
)

SOURCE = "https://example.com"


@dataclass
class Response:
    content: bytes

    @property
    def text(self):
        return self.content

    def json(self):
        return json.loads(self.content)


def test_html_page():
    p = HtmlPage(source=URL(SOURCE))
    p.response = Response(b"<html><a href='/test'>link</a></html>")
    p.postprocess_response()
    # test existence of page.root
    link = p.root.xpath("//a")[0]
    # test that links were normalized to example.com
    assert link.get("href") == "https://example.com/test"


def test_xml_page():
    p = XmlPage(source=SOURCE)
    p.response = Response(b"<data><is><nested /></is></data>")
    p.postprocess_response()
    assert p.root.tag == "data"


def test_json_page():
    nested = {"data": {"is": "nested"}}
    p = JsonPage(source=SOURCE)
    p.response = Response(json.dumps(nested))
    p.postprocess_response()
    assert p.data == nested


def test_csv_list_page():
    p = CsvListPage(source=SOURCE)
    p.response = Response("a,b,c\n1,2,3\n4,5,6")
    p.postprocess_response()
    data = list(p.process_page())
    assert len(data) == 2
    assert data[0] == {"a": "1", "b": "2", "c": "3"}


def test_html_list_page():
    p = HtmlListPage(source=SOURCE)
    p.selector = XPath("//li/text()")
    p.response = Response("<ul><li>one</li><li>two</li><li>three</li></ul>")
    p.postprocess_response()
    data = list(p.process_page())
    assert len(data) == 3
    assert data == ["one", "two", "three"]


def test_xml_list_page():
    p = XmlListPage(source=SOURCE)
    p.selector = XPath("//item/text()")
    p.response = Response(
        "<resp><item>one</item><item>two</item><item>three</item></resp>"
    )
    p.postprocess_response()
    data = list(p.process_page())
    assert data == ["one", "two", "three"]


def test_json_list_page():
    p = JsonListPage(source=SOURCE)
    p.response = Response(json.dumps(["one", "two", "three"]))
    p.postprocess_response()
    data = list(p.process_page())
    assert data == ["one", "two", "three"]
