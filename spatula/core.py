import os
import glob
import datetime
from typing import Optional
import requests
import scrapelib
from utils import dump_obj


class Workflow:
    def __init__(self, initial_page, page_processors=None, *, scraper: scrapelib.Scraper = None):
        self.initial_page = initial_page
        if not isinstance(page_processors, (list, tuple)):
            self.page_processors = [page_processors]
        else:
            self.page_processors = page_processors
        if not scraper:
            self.scraper = scrapelib.Scraper()

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

        self.initial_page._fetch_data(self.scraper)
        for i, item in enumerate(self.initial_page.process_page()):
            data = item
            for pp_cls in self.page_processors:
                page = pp_cls(data)
                page._fetch_data(self.scraper)
                data = page.process_page()
            count += 1
            dump_obj(data.to_dict(), output_dir=output_dir)
        print(f"success: wrote {count} objects to {output_dir}")


class Source:
    pass


class URL(Source):
    def __init__(self, url: str, method: str = "GET", data: dict = None, headers: dict = None):
        self.url = url
        self.method = method
        self.data = data
        self.headers = headers

    def get_response(self, scraper: scrapelib.Scraper) -> Optional[requests.models.Response]:
        return scraper.request(
            method=self.method, url=self.url, data=self.data, headers=self.headers
        )

    def __str__(self) -> str:
        return self.url


class NullSource(Source):
    def get_response(self, scraper: scrapelib.Scraper) -> Optional[requests.models.Response]:
        return None

    def __str__(self) -> str:
        return self.__class__.__name__
