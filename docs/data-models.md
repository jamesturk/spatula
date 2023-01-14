# Data Models

## Why Use Data Models?

Back in [Chaining Pages Together](scraper-basics.md#chaining-pages-together) we saw that when chaining pages we can pass data through from the parent page.

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

Dictionaries seem to work well for this since we can decide what data we want to grab on each page and combine them easily, but as scrapers tend to evolve over time it can be nice to have something a bit more self-documenting, and add the possibility to validate the data we're collecting.

That's where we can introduce `dataclasses`, `attrs`, or `pydantic` models:

=== "dataclasses"

    ``` python
    from dataclasses import dataclass

    @dataclass
    class Employee:
        first: str
        last: str
        position: str
        status: str
        hired: str
    ```

=== "attrs"

    ``` python
    import attr

    @attr.s(auto_attribs=True)
    class Employee:
        first: str
        last: str
        position: str
        status: str
        hired: str
    ```

=== "pydantic"

    ``` python
    from pydantic import BaseModel

    class Employee(BaseModel):
        first: str
        last: str
        position: str
        status: str
        hired: str
    ```

!!! question "Aren't sure which one to pick?"

    [`dataclasses`](https://docs.python.org/3/library/dataclasses.html) are built in to Python and easy to start with.
    You'll notice the examples barely differ, so it is easy to switch between them later on.

    If you want to add validation, [`pydantic`](https://pydantic-docs.helpmanual.io/) is a great choice.

And then we'll update `EmployeeDetail.process_page` to return our new `Employee` class:

``` python hl_lines="4"
    def process_page(self):
        status = CSS("#status").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return Employee(
            status=status.text,
            hired=hired.text,
            # self.input is the data passed in from the prior scrape,
            # in this case a dict we can expand here
            **self.input,
        )
```

Let's give this a run:

``` console
$ spatula test quickstart.EmployeeDetail --source "https://scrapple.fly.dev/staff/52"
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/52
Traceback (most recent call last):
...
TypeError: __init__() missing 3 required positional arguments: 'first', 'last', and 'position'
```

Of course!  We're expecting `self.input` to contain these values, but when we're running `spatula test` it doesn't know what data would have been passed in.

## Defining `input_type`

*spatula* provides a way to make the dependency on `self.input` more explicit, and restore our ability to test as a bonus side effect.

Let's add a new data model that just includes the fields we're getting from the `EmployeeList` page:

=== "dataclasses"

    ``` python
    @dataclass
    class PartialEmployee:
        first: str
        last: str
        position: str
    ```

=== "attrs"

    ``` python
    @attr.s(auto_attribs=True)
    class PartialEmployee:
        first: str
        last: str
        position: str
    ```

=== "pydantic"

    ``` python
    class PartialEmployee(BaseModel):
        first: str
        last: str
        position: str
    ```

And then we'll update `PersonDetail` to set an `input_type` and stop assuming `self.input` is a `dict`:

``` python hl_lines="2 8-10"
class EmployeeDetail(HtmlPage):
    input_type = PartialEmployee

    def process_page(self):
        status = CSS("#status").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return Employee(
            first=self.input.first,
            last=self.input.last,
            position=self.input.position,
            status=status.text,
            hired=hired.text,
        )
```

And now when we re-run the test command:

``` console
$ spatula test quickstart.EmployeeDetail --source "https://scrapple.fly.dev/staff/52"
EmployeeDetail expects input (PartialEmployee):
  first: ~first
  last: ~last
  position: ~position
INFO:quickstart.EmployeeDetail:fetching https://scrapple.fly.dev/staff/52
Employee(first='~first', last='~last', position='~position', status='Current', hired='3/6/1963')
```

Test data has been used, so even though `EmployeeList` didn't pass data into `EmployeeDetail` we can still see roughly what the data would look like if it had.

### Using Inheritance

The above pattern is pretty useful & common.
Often part of the data comes from one page, and the rest from another (or perhaps even more).

A nice way to handle this without introducing a ton of redundancy is by setting up your models to inherit from one another:

=== "dataclasses"

    ``` python
    from dataclasses import dataclass

    @dataclass
    class PartialEmployee:
        first: str
        last: str
        position: str

    @dataclass
    class Employee(PartialEmployee):
        status: str
        hired: str
    ```

=== "attrs"

    ``` python
    import attr

    @attr.s(auto_attribs=True)
    class Employee:
        first: str
        last: str
        position: str

    @attr.s(auto_attribs=True)
    class PartialEmployee(Employee):
        status: str
        hired: str
    ```

=== "pydantic"

    ``` python
    from pydantic import BaseModel

    class PartialEmployee(BaseModel):
        first: str
        last: str
        position: str

    class Employee(PartialEmployee):
        status: str
        hired: str
    ```

!!! warning
    Be sure to remember to decorate the derived class(es) if using `dataclasses` or `attrs`.

### Fixing `EmployeeList`

Don't forget to have `EmployeeList` return a `PartialEmployee` instance now instead of a `dict`:

``` python hl_lines="6"
    def process_item(self, item):
        # this function is called for each <tr> we get from the selector
        # we know there are 4 <tds>
        first, last, position, details = item.getchildren()
        return EmployeeDetail(
            PartialEmployee(
                first=first.text,
                last=last.text,
                position=position.text,
            ),
            source=XPath("./a/@href").match_one(details),
        )
```

## Overriding Default Values

Sometimes you may want to override default values (especially useful if the behavior of the second scrape varies on data from the first).

### via Command Line

The `--data` flag to `spatula test` allows overriding input values with key=value pairs.

``` console
$ spatula test quickstart.EmployeeDetail --source "https://scrapple.fly.dev/staff/52" --data first=John --data last=Neptune
EmployeeDetail expects input (PartialEmployee):
  first: John
  last: Neptune
  position: ~position
INFO:ex03_data.EmployeeDetail:fetching https://scrapple.fly.dev/staff/52
Employee(first='John', last='Neptune', position='~position', status='Current', hired='3/6/1963')
```

Alternately, `--interactive` will prompt for input data.

### via `example_input`

You can also provide the `example_input` attribute on the class in question.  This value is assumed to be of type `example_type`.

For example:

``` python hl_lines="3"
class EmployeeDetail(HtmlPage):
    input_type = PartialEmployee
    example_input = PartialEmployee("John", "Neptune", "Engineer")
```

## `example_source`

Like the above `example_input` you can define `example_source` to set a default value for the `--source` parameter when invoking `spatula test`

``` python hl_lines="4"
class EmployeeDetail(HtmlPage):
    input_type = PartialEmployee
    example_input = PartialEmployee("John", "Neptune", "Engineer")
    example_source = "https://scrapple.fly.dev/staff/52"
```

!!! warning
    Be sure not to confuse `source` with `example_source`.  The former is used whenever
    the class is invoked without a `source` parameter, while `example_source` is only used
    when running `spatula test`.

## `get_source_from_input`

It is not uncommon to want to capture a URL as part of the data and then use that URL as the next `source`.

Let's go ahead and modify `PartialEmployee` to collect a URL:

=== "dataclasses"

    ``` python hl_lines="6"
    @dataclass
    class PartialEmployee:
        first: str
        last: str
        position: str
        url: str
    ```

=== "attrs"

    ``` python hl_lines="6"
    @attr.s(auto_attribs=True)
    class PartialEmployee:
        first: str
        last: str
        position: str
        url: str
    ```

=== "pydantic"

    ``` python hl_lines="5"
    class PartialEmployee(BaseModel):
        first: str
        last: str
        position: str
        url: str
    ```

And then we'll modify `EmployeeList.process_item` to capture this URL, and stop providing a redundant `source`:

``` python hl_lines="10"
    def process_item(self, item):
        # this function is called for each <tr> we get from the selector
        # we know there are 4 <tds>
        first, last, position, details = item.getchildren()
        return EmployeeDetail(
            PartialEmployee(
                first=first.text,
                last=last.text,
                position=position.text,
                url=XPath("./a/@href").match_one(details),
            ),
        )
```

And finally, add a `get_source_from_input` method to `EmployeeDetail` (as well as updating the other uses of `Employee` to have URL):

``` python hl_lines="7 10-11 20"
class EmployeeDetail(HtmlPage):
    input_type = PartialEmployee
    example_input = PartialEmployee(
        "John",
        "Neptune",
        "Engineer",
        "https://scrapple.fly.dev/staff/1",
    )

    def get_source_from_input(self):
        return self.input.url

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
        )
```

Of course, if you have a more complex situation you can do whatever you like in `get_source_from_input`.

## Data Models As Output

When running `spatula scrape` data is written to disk as JSON.
The exact method of obtaining that JSON varies a bit depending on what type of output you have:

Raw `dict`:    Output will match exactly.

`dataclasses`:  [`dataclass.asdict`](https://docs.python.org/3/library/dataclasses.html#dataclasses.asdict) will be used.

`attrs`: [`attr.asdict`](https://www.attrs.org/en/stable/api.html) will be used to obtain a serializable representation.

`pydantic`: the model's [`dict()`](https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeldict) method will be used.

By default the filename will be a UUID, but if you wish to provide your own filename you can add a `get_filename` method to your model.

!!! warning
    When providing `get_filename` be sure that your filenames are still unique (you may wish to still incorporate a UUID if you don't have a key you're sure is unique).  *spatula* does not check for this, so you may overwrite data if your `get_filename` function does not guarantee uniqueness.
