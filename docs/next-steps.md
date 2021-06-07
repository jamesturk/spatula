# Next Steps

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
INFO:quickstart.EmployeeList:fetching https://yoyodyne-propulsion.herokuapp.com/staff
1: {'first': 'John', 'last': 'Barnett', 'position': 'Scheduling'}
...
paginating for EmployeeList source=https://yoyodyne-propulsion.herokuapp.com/staff?page=2
INFO:quickstart.EmployeeList:fetching https://yoyodyne-propulsion.herokuapp.com/staff?page=2
...
45: EmployeeDetail(input={'first': 'John', 'last': 'Ya Ya', 'position': 'Computer Design Specialist'} source=https://yoyodyne-propulsion.herokuapp.com/staff/101)
```

## Error Handling

Now that we're grabbing all 45 employees, kick off another full scrape:

``` console
$ spatula scrape quickstart.EmployeeList
INFO:quickstart.EmployeeList:fetching https://yoyodyne-propulsion.herokuapp.com/staff
...
INFO:quickstart.EmployeeDetail:fetching https://yoyodyne-propulsion.herokuapp.com/staff/404
Traceback (most recent call last):
...
scrapelib.HTTPError: 404 while retrieving https://yoyodyne-propulsion.herokuapp.com/staff/404
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
INFO:quickstart.EmployeeList:fetching https://yoyodyne-propulsion.herokuapp.com/staff
...
WARNING:quickstart.EmployeeDetail:404 while retrieving https://yoyodyne-propulsion.herokuapp.com/staff/404
...
INFO:quickstart.EmployeeDetail:fetching https://yoyodyne-propulsion.herokuapp.com/staff/101
success: wrote 44 objects to _scrapes/2021-06-03/002
```

## Defining Scraper Input

TODO: introduce validation and CLI testing

## Making Testing Better

TODO: add more ways to make testing work

## Workflows

TODO: figure out what if anything to teach on these

Now that you've seen the basics, you might want to read a bit more
about *spatula*'s `Design Philosophy`, or `API Reference`.
