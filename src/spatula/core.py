import os
import json
import glob
import datetime
import uuid
from typing import Optional
import requests
import scrapelib


class HandledError(Exception):
    def __init__(self, original):
        self.original = original


class Workflow:
    """
    Define a complete workflow by which items can be scraped and saved to disk.
    """

    def __init__(
        self, initial_page, page_processors=None, *, scraper: scrapelib.Scraper = None
    ):
        self.initial_page = initial_page
        if page_processors is None:
            self.page_processors = []
        elif not isinstance(page_processors, (list, tuple)):
            self.page_processors = [page_processors]
        else:
            self.page_processors = page_processors
        if not scraper:
            self.scraper = scrapelib.Scraper()

    def get_new_filename(self, obj):
        return str(uuid.uuid4())

    def save_object(self, obj, output_dir):
        filename = os.path.join(output_dir, self.get_new_filename(obj))
        with open(filename, "w") as f:
            json.dump(obj, f)

    def execute(self, output_dir: str = None) -> None:
        count = 0
        if not output_dir:
            dirn = 1
            today = datetime.date.today().strftime("%Y-%m-%d")
            while True:
                try:
                    output_dir = f"_scrapes/{today}/{dirn:03d}"
                    os.makedirs(output_dir)
                    break
                except FileExistsError:
                    dirn += 1
        else:
            try:
                os.makedirs(output_dir)
            except FileExistsError:
                if len(glob.glob(output_dir + "/*")):
                    raise FileExistsError(f"{output_dir} exists and is not empty")

        count = 0
        for data in self.yield_items():
            if isinstance(data, dict):
                dd = data
            else:
                dd = data.to_dict()
            self.save_object(dd, output_dir=output_dir)
        print(f"success: wrote {count} objects to {output_dir}")

    def yield_items(self):
        self.initial_page._fetch_data(self.scraper)
        for i, item in enumerate(self.initial_page.process_page()):
            data = item
            try:
                for pp_cls in self.page_processors:
                    page = pp_cls(data)
                    page._fetch_data(self.scraper)
                    data = page.process_page()
            except HandledError:
                continue
            yield data


class Source:
    pass


class URL(Source):
    """
    Defines a resource to fetch via URL, particularly useful for handling non-GET requests.

    :param url: URL to fetch
    :param method: HTTP method to use, defaults to "GET"
    :param data: POST data to include in request body.
    :param headers: dictionary of HTTP headers to set for the request.
    """

    def __init__(
        self, url: str, method: str = "GET", data: dict = None, headers: dict = None
    ):
        self.url = url
        self.method = method
        self.data = data
        self.headers = headers

    def get_response(
        self, scraper: scrapelib.Scraper
    ) -> Optional[requests.models.Response]:
        return scraper.request(
            method=self.method, url=self.url, data=self.data, headers=self.headers
        )

    def __str__(self) -> str:
        return self.url


class NullSource(Source):
    """
    Special class to set as a page's :py:attr:`source` to indicate no HTTP request needs
    to be performed.
    """

    def get_response(
        self, scraper: scrapelib.Scraper
    ) -> Optional[requests.models.Response]:
        return None

    def __str__(self) -> str:
        return self.__class__.__name__
