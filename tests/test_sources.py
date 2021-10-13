import pytest
from spatula import URL
from scrapelib import Scraper


def test_source_no_timeout():
    source = URL("https://httpbin.org/delay/1")
    assert source.get_response(Scraper()).status_code == 200


def test_source_timeout():
    source = URL("https://httpbin.org/delay/1", timeout=0.1)
    with pytest.raises(OSError):
        source.get_response(Scraper())
