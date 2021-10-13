from typing import Optional
import requests
import scrapelib


class Source:
    pass


class URL(Source):
    def __init__(
        self,
        url: str,
        method: str = "GET",
        data: dict = None,
        headers: dict = None,
        verify: bool = True,
        timeout: Optional[float] = None,
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
        """

        self.url = url
        self.method = method
        self.data = data
        self.headers = headers
        self.verify = verify
        self.timeout = timeout

    def get_response(
        self, scraper: scrapelib.Scraper
    ) -> Optional[requests.models.Response]:
        return scraper.request(
            method=self.method,
            url=self.url,
            data=self.data,
            headers=self.headers,
            verify=self.verify,
            timeout=self.timeout,
        )

    def __str__(self) -> str:
        return self.url


class NullSource(Source):
    """
    Special class to set as a page's `source` to indicate no HTTP request needs
    to be performed.
    """

    def get_response(
        self, scraper: scrapelib.Scraper
    ) -> Optional[requests.models.Response]:
        return None

    def __str__(self) -> str:
        return self.__class__.__name__
