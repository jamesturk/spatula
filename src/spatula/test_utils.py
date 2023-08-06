import json
import os
import re
import requests
import scrapelib
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from .pages import Page
from .sources import URL


class SpatulaTestError(Exception):
    pass


class CachedTestURL(URL):
    def __init__(
        self,
        url: str,
        method: str = "GET",
        data: dict = None,
        headers: dict = None,
        verify: bool = True,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
    ):
        """
        Defines a resource to fetch via URL, particularly useful for handling non-GET
        requests.

        :param url: URL to fetch
        :param method: HTTP method to use, defaults to "GET"
        :param data: POST data to include in request body.
        :param headers: dictionary of HTTP headers to set for the request.
        :param verify: bool indicating whether or not to verify SSL certificates for request, defaults to True
        :param timeout: HTTP(S) timeout in seconds
        :param retries: number of retries to make
        """

        self.url = url
        self.method = method
        self.data = data
        self.headers = headers
        self.verify = verify
        self.timeout = timeout
        self.retries = retries

    @classmethod
    def from_url(cls, url: URL | str) -> "CachedTestURL":
        if isinstance(url, str):
            url = URL(url)
        return cls(
            url=url.url,
            method=url.method,
            data=url.data,
            headers=url.headers,
            verify=url.verify,
            timeout=url.timeout,
            retries=url.retries,
        )

    def get_response(
        self, scraper: scrapelib.Scraper
    ) -> requests.models.Response:
        path = _source_to_test_path(self)
        if path.exists():
            resp = requests.models.Response()
            resp._content = path.read_bytes()
            return resp
        else:
            if os.environ.get("SPATULA_TEST_ALLOW_FETCH") == "1":
                warnings.warn(f"spatula test fetching {self} -> {path}")
                response = super().get_response(scraper)
                if not path.parent.exists():
                    path.parent.mkdir()
                with path.open("w") as cf:
                    cf.write(response.text)
                    resp = requests.models.Response()
                    resp._content = response.content
                    return resp
            else:
                warnings.warn("Set SPATULA_TEST_ALLOW_FETCH=1 to allow fetching.")
                raise SpatulaTestError(f"spatula test missing {self} @ {path}")

    def __repr__(self) -> str:
        return f"CachedTestURL({self.url})"


def _source_to_test_path(source: URL) -> Path:
    # TODO: do this the right way
    clean_url = re.sub(r"[:/]", "_", source.url)
    return Path(__file__).parent / "_test_responses" / clean_url


def cached_page_response(page: Page) -> Page:
    scraper = scrapelib.Scraper()
    if isinstance(page.source, URL):
        page.source = CachedTestURL.from_url(page.source)
    page._fetch_data(scraper)
    page.postprocess_response()
    return page


def cached_page_items(page: Page) -> list:
    if isinstance(page.source, URL):
        page.source = CachedTestURL.from_url(page.source)
    items = list(page.do_scrape())
    return items
