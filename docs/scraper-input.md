# Scraper Input


## Data Models

Back in [scraper-basics.md#chaining-pages-together] we saw that when chaining pages we can pass data through from the parent page.

``` python hl_lines="10 11 12"
class EmployeeDetail(HtmlPage):
    def process_page(self):
        marital_status = CSS("#status").match_one(self.root)
        children = CSS("#children").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return dict(
            marital_status=marital_status.text,
            children=children.text,
            hired=hired.text,
            # self.input is the data passed in from the prior scrape,
            # in this case a dict we can expand here
            **self.input,
        )
```

Dictionaries seem to work well for this since we can decide what data we want to grab on each page and combine them easily, but as scrapers tend to evolve over time it can be nice to have something a bit more self-documenting.

That's where we can introduce `dataclasses`, `attrs`, or `pydaantic` models:

=== "dataclasses"

    ``` python
    from dataclasses import dataclass

    @dataclass
    class Employee:
        first: str
        last: str
        position: str
        marital_status: str
        children: int
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
        marital_status: str
        children: int
        hired: str
    ```

=== "pydantic"

    ``` python
    from pydantic import BaseModel

    class Employee(BaseModel):
        first: str
        last: str
        position: str
        marital_status: str
        children: int
        hired: str
    ```

And then we'll update `EmployeeDetail.process_page` to return our new `Employee` class:

``` python hl_lines="5"
    def process_page(self):
        marital_status = CSS("#status").match_one(self.root)
        children = CSS("#children").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return Employee(
            marital_status=marital_status.text,
            children=children.text,
            hired=hired.text,
            # self.input is the data passed in from the prior scrape,
            # in this case a dict we can expand here
            **self.input,
        )
```

Let's give this a run:

``` console
$ spatula test quickstart.EmployeeDetail --source "https://yoyodyne-propulsion.herokuapp.com/staff/52"
INFO:quickstart.EmployeeDetail:fetching https://yoyodyne-propulsion.herokuapp.com/staff/52
Traceback (most recent call last):
...
TypeError: __init__() missing 3 required positional arguments: 'first', 'last', and 'position'
```

Of course!  We're expecting `self.input` to contain these values, but when we're running `spatula test` it doesn't know what data would have been passed in.

## Defining `input_type`

It is common to have the final data object dependent upon input data in some way.

*spatula* provides a way to make the dependency on `self.input` more explicit, and restore our ability to test as a bonus side effect.

Let's add a new data model that just includes the fields we're getting from the `EmployeeList` page:


=== "dataclasses"

    ``` python
    @dataclass
    class PartialEmployee:
        first: str
        last: str
        }
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

``` python hl_lines="2 9-11"
class EmployeeDetail(HtmlPage):
    input_type = PartialEmployee

    def process_page(self):
        marital_status = CSS("#status").match_one(self.root)
        children = CSS("#children").match_one(self.root)
        hired = CSS("#hired").match_one(self.root)
        return Employee(
            first=self.input.first,
            last=self.input.last,
            position=self.input.position,
            marital_status=marital_status.text,
            children=children.text,
            hired=hired.text,
        )
```


And now when we re-run the test command:

``` console
$ spatula test quickstart.EmployeeDetail --source "https://yoyodyne-propulsion.herokuapp.com/staff/52"
EmployeeDetail expects input (PartialEmployee):
  first: ~first
  last: ~last
  position: ~position
INFO:quickstart.EmployeeDetail:fetching https://yoyodyne-propulsion.herokuapp.com/staff/52
Employee(first='~first', last='~last', position='~position', marital_status='Married', children='1', hired='3/6/1963')
```

Test data has been used, so even though `EmployeeList` didn't pass data into `EmployeeDetail` we can still see roughly what the data would look like if it had.

## Overriding Default Values

Sometimes you may want to override default values (especially useful if the behavior of the second scrape varies on data from the first).

### via Command Line

The `--data` flag to `spatula test` allows overriding input values with key=value pairs.

``` console
$ spatula test quickstart.EmployeeDetail --source "https://yoyodyne-propulsion.herokuapp.com/staff/52" --data first=John --data last=Neptune
EmployeeDetail expects input (PartialEmployee):
  first: John
  last: Neptune
  position: ~position
INFO:ex03_data.EmployeeDetail:fetching https://yoyodyne-propulsion.herokuapp.com/staff/52
Employee(first='John', last='Neptune', position='~position', marital_status='Married', children='1', hired='3/6/1963')
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

## Making Testing Better

TODO: add more ways to make testing work

## Workflows

TODO: figure out what if anything to teach on these

Now that you've seen the basics, you might want to read a bit more
about *spatula*'s `Design Philosophy`, or `API Reference`.
