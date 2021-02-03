import json
from dataclasses import dataclass
from spatula import HtmlPage, XmlPage, JsonPage  # TODO PdfPage

# from spatula import CsvListPage, HtmlListPage, XmlListPage, JsonListPage

SOURCE = "https://example.com"


@dataclass
class Response:
    content: bytes

    def json(self):
        return json.loads(self.content)


def test_html_page():
    p = HtmlPage(source=SOURCE)
    p.response = Response(b"<html><a href='/test'>link</a></html>")
    p.postprocess_response()
    # test existence of page.root
    link = p.root.xpath("//a")[0]
    # test that links were normalized to example.com
    link.get("href") == "https://example.com/test"


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
