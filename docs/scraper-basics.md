# A First Scraper

This guide contains quick examples of how you could scrape a small list
of employees of the fictional [Yoyodyne Propulsion
Systems](https://scrapple.fly.dev/staff), a site developed
for demonstrating web scraping. This will give you an idea of what it
looks like to write a scraper using *spatula*.

## Scraping a List Page

It is fairly common for a scrape to begin on some sort of directory or
listing page.

We'll start by scraping the staff list on
<https://scrapple.fly.dev/staff>

This page has a fairly simple HTML table with four columns:

``` html
<table id="employees">
  <thead>
    <tr>
      <th>First Name</th>
      <th>Last Name</th>
      <th>Position Name</th>
      <th>&nbsp;</th>
    </tr>
  </thead>
  <tbody>
  <tr>
    <td>Eric</td>
    <td>Sound</td>
    <td>Manager</td>
    <td><a href="/staff/52">Details</a></td>
  </tr>
  <tr>
    <td>Jane</td>
    <td>Daikon</td>
    <td>Developer</td>
    <td><a href="/staff/2">Details</a></td>
  </tr>

  ...continues...
```

*spatula* provides a special interface for these cases. See below how
we process each matching link by deriving from a `HtmlListPage`
and providing a `selector` as well as a `process_item`  method.

Open a file named quickstart.py and add the following code:

``` python
# imports we'll use in this example
from spatula import (
    HtmlPage, HtmlListPage, CSS, XPath, SelectorError
)


class EmployeeList(HtmlListPage):
    source = "https://scrapple.fly.dev/staff"

    # each row represents an employee
    selector = CSS("#employees tbody tr")

    def process_item(self, item):
        # this function is called for each <tr> we get from the selector
        # we know there are 4 <tds>
        first, last, position, details = item.getchildren()
        return dict(
            first=first.text,
            last=last.text,
            position=position.text,
        )
```

One concept in spatula is that we typically write one class per type of
page we encounter. This class defines the logic to process the employee
list page. This class will turn each row on the page into a dictionary
with the 'first', 'last', and 'position' keys.

It can be tested from the command line like:

``` console
$ spatula test quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff
1: {'first': 'Eric', 'last': 'Sound', 'position': 'Manager'}
2: {'first': 'Jane', 'last': 'Daikon', 'position': 'Developer'}
...
10: {'first': 'Ashley', 'last': 'Wilson', 'position': 'Engineer'}
```

The `spatula test` command lets us quickly see the output of the part of
the scraper we're working on.

You may notice that we're only grabbing the first page for now, we'll
come back in a bit to handle pagination.

## Scraping a Single Page

Employees have a few more details not included in the table on pages
like <https://scrapple.fly.dev/staff/52>.

We're going to pull some data elements from the page that look like:

``` html
<h2 class="section">Employee Details for Eric Sound</h2>
<div class="section">
  <dl>
    <dt>Position</dt>
    <dd id="position">Scheduling</dd>
    <dt>Status</dt>
    <dd id="status">Current</dd>
    <dt>Hired</dt>
    <dd id="hired">3/6/1963</dd>
  </dl>
</div>
```

To demonstrate extracting the details from this page, we'll write a
small class to handle individual employee pages.

Whereas before we used `HtmlListPage` and overrode `process_item`, this time
we'll subclass `HtmlPage`, and override the `process_page` function.

``` python
class EmployeeDetail(HtmlPage):
    def process_page(self):
        status = CSS("#status").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return dict(
            status=status.text,
            hired=hired.text,
        )
```

This will extract the elements from the page and return them in a dictionary.

It can be tested from the command line like:

``` console
$ spatula test quickstart.EmployeeDetail --source "https://scrapple.fly.dev/staff/52"
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/52
{'hired': '3/6/1963', 'status': 'Current'}
```

One thing to note is that since we didn't define a single source attribute like we did in `EmployeeList`, we need to pass one on the command line with `--source`.
This lets you quickly try your scraper against multiple variants of a page as needed.

## Chaining Pages Together

Most moderately complex sites will require chaining data together from
multiple pages to get a complete object.

Let's revisit `EmployeeList` and have it return instances of `EmployeeDetail`
to tell *spatula* that more work is needed:

``` python hl_lines="13 19 20"
class EmployeeList(HtmlListPage):
     # by providing this here, it can be omitted on the command line
     # useful in cases where the scraper is only meant for one page
     source = "https://scrapple.fly.dev/staff"

     # each row represents an employee
     selector = CSS("#employees tbody tr")

     def process_item(self, item):
         # this function is called for each <tr> we get from the selector
         # we know there are 4 <tds>
         first, last, position, details = item.getchildren()
         return EmployeeDetail(
             dict(
                 first=first.text,
                 last=last.text,
                 position=position.text,
             ),
             source=XPath("./a/@href").match_one(details),
         )
```

And we can revisit `EmployeeDetail` to tell it to combine the data it collects with the data passed in from the parent page:

``` python hl_lines="8 9 10"
class EmployeeDetail(HtmlPage):
    def process_page(self):
        status = CSS("#status").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return dict(
            status=status.text,
            hired=hired.text,
            # self.input is the data passed in from the prior scrape,
            # in this case a dict we can expand here
            **self.input,
        )
```

Now a run looks like:

``` console
$ spatula test quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff
1: EmployeeDetail(input={'first': 'Eric', 'last': 'Sound', 'position': 'Manager'} source=https://scrapple.fly.dev/staff)
2: EmployeeDetail(input={'first': 'Jane', 'last': 'Daikon', 'position': 'Developer'} source=https:/scrapple.fly.dev/staff/2)
...
10: EmployeeDetail(input={'first': 'Ashley', 'last': 'Wilson', 'position': 'Engineer'} source=https:/scrapple.fly.dev/staff/20)
```

By default, `spatula test` just shows the result of the page you're
working on, but you can see that it is now returning page objects with
the data and a `source` set.

## Running a Scrape

Now that we're happy with our individual page scrapers, we can run the
full scrape and write the data to disk.

For this we use the `spatula scrape` command:

``` console
$ spatula scrape quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/52
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/2
...
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/100
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/101
success: wrote 10 objects to _scrapes/2021-06-03/001
```

And now our scraped data is on disk, ready for you to use!

If you look at a data file you'll see that it has the full data for an
individual:

``` json
{
  "status": "Support",
  "hired": "9/9/1963",
  "first": "Emily",
  "last": "Parker",
  "position": "Support"
}
```

## Using spatula Within Other Scripts

Perhaps you don't want to write your output to disk.
If you want to post-process your data further or use it as part of a larger pipeline a page's `do_scrape` method lets you do just that.  It returns a generator that you can use to process items as you see fit.

For example:

```python
page = EmployeeList()
for e in page.do_scrape():
    print(e)
```

You an do whatever you wish with these results, output them in a custom format, save them to your database, etc.

## Pagination

While writing the list page we ignored pagination, let's go ahead and
add it now.

If we override the `get_next_source`
method on our `EmployeeLList` class,
*spatula* will continue to the next page once it has called
`process_item` on all elements on the current page.

``` python
# add this within EmployeeList
def get_next_source(self):
    try:
        return XPath("//a[contains(text(), 'Next')]/@href").match_one(self.root)
    except SelectorError:
        pass
```

You'll notice the output of `spatula test quickstart.EmployeeList` has now changed:

``` console
$ spatula test quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff
1: {'first': 'Eric', 'last': 'Sound', 'position': 'Manager'}
...
paginating for EmployeeList source=https://scrapple.fly.dev/staff?page=2
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff?page=2
...
45: EmployeeDetail(input={'first': 'Oscar', 'last': 'Ego', 'position': 'Outreach Coordinator'} source=https://scrapple.fly.dev/staff/101)
```

## Error Handling

Now that we're grabbing all 45 employees, kick off another full scrape:

``` console
$ spatula scrape quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff
...
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/404
Traceback (most recent call last):
...
scrapelib.HTTPError: 404 while retrieving https://scrapple.fly.dev/staff/404
```

An error! It turns out that one of the employee pages isn't loading correctly.

Sometimes it is best to let these errors propagate so you can try to fix
the broken scraper.

Other times it makes more sense to handle the error and move on. If you
wish to do that, you can override
`process_error_response`.

Add the following to `EmployeeDetail`:

``` python
def process_error_response(self, exception):
    # every Page subclass has a built-in logger object
    self.logger.warning(exception)
```

Run the scrape again to see this in action:

``` console
$ spatula scrape quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://scrapple.fly.dev/staff
...
WARNING:quickstart.EmployeeDetail:404 while retrieving https://scrapple.fly.dev/staff/404
...
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/101
success: wrote 44 objects to _scrapes/2021-06-03/002
```
