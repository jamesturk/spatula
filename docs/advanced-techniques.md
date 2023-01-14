# Advanced Techniques

## Specifying Dependencies

While the pattern laid out in [Scraper Basics](scraper-basics.md) is fairly common,
sometimes data is laid out in other ways that doesn't fit as neatly with the list & detail page workflow.

For example, take a look at the page <https://scrapple.fly.dev/awards>, which lists some awards that some Yoyodyne employees have won.

In some cases you may decide to scrape this data separately using the typical `HtmlListPage` approach, but let's say you want each employee to have a list of their awards as part of the `EmployeeList`/`EmployeeDetail` scrape.

### Scraping the New Page

First let's write a quick page scraper to grab the award name & year and associate them with a person's name:

``` python
# add to imports
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class Award:
    award: str
    year: str


class AwardsPage(HtmlPage):
    source = "https://scrapple.fly.dev/awards"

    def process_page(self):
        # augmentation pages will almost always return some kind of dictionary
        mapping = defaultdict(list)

        award_cards = CSS(".card .large", num_items=9).match(self.root)
        for item in award_cards:
            award = CSS("h2").match_one(item).text.strip()
            year = CSS("small").match_one(item).text
            # make sure we got exactly 2 <dd> tags, and we take the second
            name = CSS("dd").match(item, num_items=2)[1].text
            # map the data based on a key we know we have elsewhere in the scrape
            mapping[name].append(Award(award=award, year=year))
        return mapping
```

Running this scrape yields a single dictionary:

``` console
$ spatula test quickstart.AwardsPage
INFO:quickstart.AwardsPage:fetching https://scrapple.fly.dev/awards
defaultdict(<class 'list'>,
    {'John Coyote': [Award(award='Album of the Year', year='1997')],
     'John Fish': [Award(award='Cousteau Society Award', year='1989')],
     'John Lee': [Award(award='Most Creative Loophole', year='1985')],
     'John Many Jars': [Award(award='2nd Place, Most Jars Category', year='1987')],
     "John O'Connor": [Award(award='Nobel Prize in Physics', year='2986')],
     'John Two Horns': [Award(award='Paralegal of the Year', year='1999')],
     'John Whorfin': [Award(award='Nobel Prize in Physics', year='1934'),
                      Award(award='Best Supporting Actor', year='1985')],
     'John Ya Ya': [Award(award='ACM Award', year='1986')]})
```

### Add the Dependency

Now that this page is working, we can connect it to our previously written `EmployeeList` scrape.

``` python hl_lines="2"
class EmployeeDetail(HtmlPage):
    dependencies = {"award_mapping": AwardsPage()}

    ...
```

This line ensures that each instance of `EmployeeDetail` will be have a `self.award_mapping` attribute, pre-populated with the result of `AwardsPage`.

If you pass an instance of a page then each `EmployeeDetail` will share a cached copy of `AwardsPage`, ensuring it is only scraped once.

### Use the Dependency Data

The final step now is to actually use the mapping to attach the awards to the employees:

``` python hl_lines="4"
class Employee(PartialEmployee):
    status: str
    hired: str
    awards: list[Award]
```

And then within `EmployeeDetail`:

``` python hl_lines="11"
    def process_page(self):
        status = CSS("#status").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return Employee(
            first=self.input.first,
            last=self.input.last,
            position=self.input.position,
            url=self.input.url,
            status=status.text,
            hired=hired.text,
            awards=self.award_mapping[f"{self.input.first} {self.input.last}"],
        )
```

We can test by passing fake data with a person that has an award:

``` console hl_lines="1 2 4"
$ spatula test quickstart.EmployeeDetail --data first=John --data last=Fish
INFO:quickstart.AwardsPage:fetching https://scrapple.fly.dev/awards
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/1
{'awards': [Award(award='Cousteau Society Award', year='1989')],
 'first': 'John',
 'hired': '10/31/1938',
 'last': 'Fish',
 'status': 'Current',
 'position': 'Engineer',
 'url': 'https://scrapple.fly.dev/staff/1'}
```

Note that before fetching the `EmployeeDetail` page, `AwardsPage` is fetched, and the `awards` data is then correctly attached to John Fish.

## Advanced Sources

### `NullSource`

Every `Page` has a `source` which is fetched when it is executed.  There are cases where you may wish to avoid that behavior.  If you set `NullSource` for a page, no HTTP request will be performed prior to the `process_item` method being called.

A common use for this is dispatching multiple detail pages without a corresponding list page.

``` python

class NebraskaPageGenerator(ListPage):
    """
    When scraping the Nebraska legislature, the pages are named
    http://news.legislature.ne.gov/dist01/
    through
    http://news.legislature.ne.gov/dist49/
    but with out an easy-to-scrape source.

    So we use this method to mimic the results that a ListPage would yield,
    without a wasted request.
    """
    source = NullSource()

    def process_page(self):
        for n in range(1, 50):
            yield NebraskaLegPage(source=f"http://news.legislature.ne.gov/dist{n:02d}/")
```

### Custom Sources

Sometimes you need a page to do something that isn't easy to do with a single `URL` object.

To derive a custom `Source`, simply override the `get_response` method in your own custom source class.

For example:

``` python
import scrapelib
import requests
from spatula import Source

class FauxFormSource(Source):
    """
    emulate a case where we need to get a hidden input value to successfully
    retrieve a form
    """
    def get_response(self, scraper: scrapelib.Scraper) -> requests.models.Response:
        url = "https://example.com/"
        resp = scraper.get(url)
        root = lxml.html.fromstring(resp.content)
        token = form.xpath(".//input[@name='csrftoken']")[0].value
        # do second request with data
        resp = scraper.post(self.url, {"csrftoken": token})
        return resp
```

You can do whatever you want within `get_response` as long as something resembling a [`requests.Response`](https://2.python-requests.org/en/master/user/advanced/#request-and-response-objects) is returned.

## Custom Page Types

Another powerful technique is to define your own `Page` or `ListPage` subclasses.

Most of the existing [page types](reference.md#pages) are fairly simple, typically only overriding `postprocess_response`, which is called after any `source` is turned into `self.response`, but before `process_item` is called.

If you wanted to use `BeautifulSoup` instead of spatula's default `lxml.html` you could define a custom `SoupPage`:

``` python
from bs4 import BeautifulSoup
from spatula import Page


class SoupPage(Page):
    def postprocess_response(self) -> None:
        # self.response is guaranteed to have been set by now
        self.soup = BeautifulSoup(self.response.content)
```

This would let any pages that derive from `SoupPage` use `self.soup` the same way that `self.root` is available on `HtmlPage`.

## Retries

Sometimes a server returns incomplete or otherwise erroneous data intermittently.  It can be useful to check if the page contains the expected data and retry after some wait period if not.

This can be done by adding a `accept_response` method to your `Page` subclass.  If `accept_response` is `False`, spatula will sleep for `spatula.config.RETRY_WAIT_SECONDS` and then retry.

By default this retry will only happen once, controlled by `spatula.config.REJECTED_RESPONSE_RETRIES`.
If you need to set a per-Source number of retries, you can also pass `retries` to `URL` like so:

``` python
RejectPartialPage(source=URL("https://openstates.org", retries=3))
```

!!! warning
    spatula.config is experimental, any use of these variables may change before 1.0 is released.

An example:

``` python

class RejectPartialPage(Page):
    def accept_response(self, response: requests.Response) -> bool:
        # sometimes the page is returned missing the footer, retry if so
        return "<footer>" in response.text
```
