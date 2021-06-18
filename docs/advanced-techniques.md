# Advanced Techniques

## Specifying Dependencies

While the pattern laid out in [Scraper Basics](scraper-basics.md) is fairly common,
sometimes data is laid out in other ways that doesn't fit as neatly with the list & detail page workflow.

For example, take a look at the page <https://yoyodyne-propulsion.herokuapp.com/awards>, which lists some awards that some Yoyodyne employees have won.

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
    source = "https://yoyodyne-propulsion.herokuapp.com/awards"

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
INFO:quickstart.AwardsPage:fetching https://yoyodyne-propulsion.herokuapp.com/awards
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

``` python hl_lines="5"
class Employee(PartialEmployee):
    marital_status: str
    children: int
    hired: str
    awards: list[Award]
```

And then within `EmployeeDetail`:

``` python hl_lines="13"
    def process_page(self):
        marital_status = CSS("#status").match_one(self.root)
        children = CSS("#children").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return Employee(
            first=self.input.first,
            last=self.input.last,
            position=self.input.position,
            url=self.input.url,
            marital_status=marital_status.text,
            children=children.text,
            hired=hired.text,
            awards=self.award_mapping[f"{self.input.first} {self.input.last}"],
        )
```

We can test by passing fake data with a person that has an award:
``` console hl_lines="1 2 4"
$ spatula test quickstart.EmployeeDetail --data first=John --data last=Fish
INFO:quickstart.AwardsPage:fetching https://yoyodyne-propulsion.herokuapp.com/awards
INFO:quickstart.EmployeeDetail:fetching https://yoyodyne-propulsion.herokuapp.com/staff/1
{'awards': [Award(award='Cousteau Society Award', year='1989')],
 'children': '0',
 'first': 'John',
 'hired': '10/31/1938',
 'last': 'Fish',
 'marital_status': 'Single',
 'position': 'Engineer',
 'url': 'https://yoyodyne-propulsion.herokuapp.com/staff/1'}
```

Note that before fetching the `EmployeeDetail` page, `AwardsPage` is fetched, and the `awards` data is then correctly attached to John Fish.
