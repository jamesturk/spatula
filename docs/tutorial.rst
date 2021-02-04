Tutorial
========

If you're new to **spatula** it might be helpful to see a complete example.

Given that **spatula** originated within `Open States <https://openstates.org>`_, we're going to scrape the members of the
Maryland legislature.

Planning A Scrape
-----------------

Like many legislatures, Maryland has two chambers, a House & Senate.

Poking around on their website we find the following two URLs:

* https://mgaleg.maryland.gov/mgawebsite/Members/Index/house
* https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate

It looks like these pages use the same HTML, so we'll need a :py:class:`HtmlListPage` subclass that handles both which we'll call :py:class:`RosterList`.

Each legislator then has a page like https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones.

This page will require a detail page scraper derived from :py:class:`HtmlPage`, which we'll call :py:class:`LegislatorDetail`.

.. note:: If the House & Senate were to use different directory formats, we'd perhaps wind up with :py:class:`SenateList` and :py:class:`HouseList`.  If individual pages were different between chambers, :py:class:`SenatorDetail` and :py:class:`DelegateDetail` might be required.  **spatula**-written scrapers should generally have one class per distinct type of page.

Now that we have a plan, we can begin working on these two components entirely in isolation of one another.  While working on a given page **spatula** provides ways to get rapid feedback on how things are working so far.  This means you can work with the :py:class:`LegislatorDetail` scraper first, before having a functioning :py:class:`RosterList` scraper.

Writing :py:class:`RosterList`
------------------------------

Looking at one of the roster pages, it looks like each member gets their own div that looks something like:

.. code-block:: html

  <div class="p-0 member-index-cell">
    <div class="container-fluid member-index-group">
      <div class="row">
        <div class="col-5 text-left">
          <a href="/mgawebsite/Members/Details/augustine01">
              <img src="/2021RS/images/augustine01.jpg" width="125" height="150">
              Augustine, Malcolm District 47 Prince George's County Democrat
          </a>
        </div>
        <div class="col-7 text-left">
          <dl>
            <dd>
              <a href="/mgawebsite/Members/Details/augustine01">Augustine, Malcolm</a><br>
              District 47 <br>
              Prince George's County <br>
              Democrat <br>
            </dd>
          </dl>
        </div>
      </div>
    </div>
  </div>

Create a new file ``maryland.py`` and add some basic imports and a new class:

.. code-block:: python

  from spatula import HtmlListPage, CSS

  class RosterList(HtmlListPage):
      selector = CSS("div.member-index-cell")

That's enough that we can check things:

.. code-block:: console

  $ spatula test maryland.RosterList --source https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate
  fetching https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate for RosterList
  0: <div class='p-0 member-index-cell'> @ line 553
  1: <div class='p-0 member-index-cell'> @ line 578
  ...
  52: <div class='p-0 member-index-cell'> @ line 2114

A few things to note:

Since :py:class:`RosterList` works for multiple URLs, we need to specify a ``source`` on the command line.

Right now we're getting unhelpful <div> output, but we might notice we're getting 53 results instead of the 47 we expect for this page.

We can refine the selector based on this feedback, let's change the selector to include ``#myDIV`` so we only get the results we expect.

While we're at it, let's add a :py:meth:`process_item` method.  All pages that derive from :py:class:`ListPage` will call this method on each subelement of the page.  (e.g. :py:class:`CsvListPage`).  Update the code to look like this:

.. code-block:: python
   :emphasize-lines: 1,4,6-14

    from spatula import HtmlListPage, CSS, XPath

    class RosterList(HtmlListPage):
        selector = CSS("#myDIV div.member-index-cell")

        def process_item(self, item):
            dd_text = XPath(".//dd/text()").match(item)
            district = dd_text[2].strip()
            party = dd_text[4].strip()
            return dict(
                district=district,
                party=party,
                url=XPath(".//dd/a[1]/@href").match_one(item),
            )

First, you'll see that we added the :py:class:`XPath` selector.
XPath is a powerful expression language that is useful for scraping.
It is completely OK to stick to :py:class:`CSS`, but some things can be more clearly expressed via XPath.

Second, we've updated :py:data:`RosterList.selector` to be more narrow.

Finally, we've added the `process_item` method.
It receives an `item` parameter which will be the results of every selector.
The method extracts a bit of content, and returns it in a dictionary.

Now let's give it a run:

.. code-block:: console

  $ spatula test maryland.RosterList --source https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate
  ...
  45: {'district': 'District 3',
   'party': 'Democrat',
   'url': 'https://mgaleg.maryland.gov/mgawebsite/Members/Details/young'}
  46: {'district': 'District 14',
   'party': 'Democrat',
   'url': 'https://mgaleg.maryland.gov/mgawebsite/Members/Details/zucker01'}

Since we're returning dictionaries, the ``test`` command pretty prints them for us.

This looks good so far, the most important thing is that we got the URL element.
You'll recognize that URL format as the one we mentioned that :py:class:`PersonDetail` will handle.
Perhaps now would be a good time to switch over to working on that.

Writing :py:class:`PersonDetail`
--------------------------------

Within the same file, first let's add some more imports we'll need:

.. code-block:: python
   :emphasize-lines: 1

    from spatula import HtmlListPage, CSS, XPath, HtmlPage, SimilarLink

And then add a new class:

.. code-block:: 

  class PersonDetail(HtmlPage):

      def process_page(self):
          # format is mailto:<addr>?subj=...
          email = SimilarLink("mailto:").match_one(self.root).get("href")
          email = email.split(":", 1)[1].split("?")[0]

          image = CSS("img.details-page-image-padding").match_one(self.root).get("src")

          return dict(
              name=CSS("h2").match_one(self.root).text,
              image=image,
              email=email,
          )

New things here to note:

* When defining a detail page scraper, you'll write a :py:meth:`process_page` method that returns data from that page.
* :py:class:`HtmlPage` provides the HTML parsed into an `lxml.etree.Element` as `self.root`
* We use yet another selector type, this time `SimilarLink`.  This grabs all links on the page that match a pattern.

We can test this class from the command line, we just need to give it a detail page URL as ``--source``:

.. code-block:: console

  $ spatula test maryland.PersonDetail --source https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones
  fetching https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones for PersonDetail
  {'email': 'adrienne.jones@house.state.md.us',
   'image': 'https://mgaleg.maryland.gov/2021RS/images/jones.jpg',
   'name': 'Delegate Adrienne A. Jones'}

Looking good!

Both of our page scrapers are returning a few fields.
:py:class:`RosterList` returns `district`, `party`, and `url` 
while :py:class:`PersonDetail` returns `email`, `image`, and `name`.

We're going to get to chaining these together in just a second.
Since `PersonDetail` is the second step in the process, we want it to do something with the data that comes from its parent page.

Before we do that, we will want to revisit :py:class:`RosterList`.

Defining Scraper Input
----------------------

While scrapers can return any type of data, it is common to start with dictionaries as we have above.

When it comes time to link scrapers together however, it is generally a good idea to be more specific.

We'll use a `dataclass <https://docs.python.org/3/library/dataclasses.html>`_ to help document what each scraper is responsible for retrieving (and provide hints to **spatula**).

Adding these lines:

.. code-block:: python
   :emphasize-lines: 1-8

    # adding these lines
    from dataclasses import dataclass

    @dataclass
    class PartialPerson:
        district: str
        party: str
        url: str

Updating the RosterList class:

.. code-block:: python
   :emphasize-lines: 8

    class RosterList(HtmlListPage):
        selector = CSS("#myDIV div.member-index-cell")

        def process_item(self, item):
            dd_text = XPath(".//dd/text()").match(item)
            district = dd_text[2].strip()
            party = dd_text[4].strip()
            return PartialPerson(
                district=district,
                party=party,
                url=XPath(".//dd/a[1]/@href").match_one(item),
            )


And finally, letting the :py:class:`PersonDetail` class know what type of input it can expect:

.. code-block:: python
   :emphasize-lines: 2

    class PersonDetail(HtmlPage):
        input_type = PartialPerson

        def process_page(self):
          ...

Let's take a look at how that changed our output:

.. code-block:: console

  $ spatula test maryland.RosterList --source https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate
  fetching https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate for RosterList
  1: PartialPerson(district='District 29', party='Republican', url='https://mgaleg.maryland.gov/mgawebsite/Members/Details/bailey01')
  ...
  46: PartialPerson(district='District 14', party='Democrat', url='https://mgaleg.maryland.gov/mgawebsite/Members/Details/zucker01')

The only change here is the type, our new PartialPerson objects display cleanly in the console, just like the dictionaries we were using before.

What about :py:class:`PersonDetail`?  Let's try it:

.. code-block:: console

  $ spatula test maryland.PersonDetail --source https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones
  PersonDetail expects input (PartialPerson): 
    district: ~district
    party: ~party
    url: ~url
  fetching https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones for PersonDetail
  {'email': 'adrienne.jones@house.state.md.us',
   'image': 'https://mgaleg.maryland.gov/2021RS/images/jones.jpg',
   'name': 'Delegate Adrienne A. Jones'}

``spatula test`` not knows that PersonDetail might need values from a parent scraper.

Since we didn't specify any (see :ref:`spatula test`), it provided defaults!

This can be really helpful, but we'll need to use the input to see how it works.

Using :py:data:`self.input`
---------------------------

When a class has an `input_type` defined, the instance of that type is available as `self.input`.

Let's use that to have our :py:meth:`PersonDetail.process_page` method return a more complete object:

.. code-block:: python
   :emphasize-lines: 15-17

    class PersonDetail(HtmlPage):
        input_type = PartialPerson

        def process_page(self):
            # format is mailto:<addr>?subj=...
            email = SimilarLink("mailto:").match_one(self.root).get("href")
            email = email.split(":", 1)[1].split("?")[0]

            image = CSS("img.details-page-image-padding").match_one(self.root).get("src")

            return dict(
                name=CSS("h2").match_one(self.root).text,
                image=image,
                email=email,
                district=self.input.district,
                party=self.input.party,
                url=self.input.url,
            )

Now let's try running it again:

.. code-block:: console

  $ spatula test maryland.PersonDetail --source https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones
  PersonDetail expects input (PartialPerson): 
    district: ~district
    party: ~party
    url: ~url
  fetching https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones for PersonDetail
  {'district': '~district',
   'email': 'adrienne.jones@house.state.md.us',
   'image': 'https://mgaleg.maryland.gov/2021RS/images/jones.jpg',
   'name': 'Delegate Adrienne A. Jones',
   'party': '~party',
   'url': '~url'}

Alright, now that data is flowing through PersonDetail.

Hopefully now the reason that **spatula** provided defaults is a bit more clear now.
Since **spatula** knows the fields that need to be provided, it can provide stub values so you can see how they'll
fit into your output.

As you can imagine, sometimes the scrape will need to make use of those values to determine what it should do, in that case you can pass them along like so::

  $ spatula test maryland.PersonDetail --source https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones -d url=https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones

But actually, we're going to take advantage of a little piece of magic here to simplify further.

It is very common to set a detail page's source to the `url` attribute of a parent object.

So common in fact, that **spatula** will assume this is the case if it gets input with a `url` property and set the source accordingly.

.. note:: This behavior can be overriden with :py:meth:`get_source_from_input`, which can return a full :py:class:`URL` source, allowing for much more sophisticated behavior.

Which means we can mimic what will happen if a valid URL is passed through to :py:class:`PersonDetail` like this:

.. code-block:: console
   :emphasize-lines: 5-6,12

    $ spatula test maryland.PersonDetail --d url=https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones
    PersonDetail expects input (PartialPerson): 
      district: ~district
      party: ~party
      url: https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones
    fetching https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones for PersonDetail
    {'district': '~district',
     'email': 'adrienne.jones@house.state.md.us',
     'image': 'https://mgaleg.maryland.gov/2021RS/images/jones.jpg',
     'name': 'Delegate Adrienne A. Jones',
     'party': '~party',
     'url': 'https://mgaleg.maryland.gov/mgawebsite/Members/Details/jones'}
 
Connecting Our Pages
--------------------

Now that our two page scrapers work separately, we can wire them together.

.. code-block:: python
   :emphasize-lines: 8-14

    class RosterList(HtmlListPage):
        selector = CSS("#myDIV div.member-index-cell")

        def process_item(self, item):
            dd_text = XPath(".//dd/text()").match(item)
            district = dd_text[2].strip()
            party = dd_text[4].strip()
            return PersonDetail(
              PartialPerson(
                  district=district,
                  party=party,
                  url=XPath(".//dd/a[1]/@href").match_one(item),
              )
            )

And let's instantiate two instances at the bottom of the file:

.. code-block:: python

  house = RosterList(source="https://mgaleg.maryland.gov/mgawebsite/Members/Index/house")
  senate = RosterList(source="https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate")

These two instances will define a starting point, our :py:class:`RosterList` instantiated with the two starting URLs.

The individual results from that scrape will then be sent one at a time as input into :py:class:`PersonDetail`.

We can run workflows with:

.. code-block:: console

    $ poetry run spatula scrape maryland.senators
    fetching https://mgaleg.maryland.gov/mgawebsite/Members/Index/senate for RosterList
    ...
    fetching https://mgaleg.maryland.gov/mgawebsite/Members/Details/zucker01 for PersonDetail
    success: wrote 47 objects to _scrapes/2021-01-19/001

If you look in this directory, there will be a bunch of JSON files that contain the full results of each scrape, for instance::

  {"name": "Senator Cory V. McCray",
   "image": "https://mgaleg.maryland.gov/2021RS/images/mccray02.jpg",
   "email": "cory.mccray@senate.state.md.us",
   "district": "District 45",
   "party": "Democrat",
   "url": "https://mgaleg.maryland.gov/mgawebsite/Members/Details/mccray02"
   }

Once this data is on disk, **spatula**'s job is done.
You can post-process these files however you want, and in the future **spatula** will provide additional output methods.
