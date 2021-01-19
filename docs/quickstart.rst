Quickstart
==========

This guide contains quick examples of how you could scrape a small list of `RFCs <https://en.wikipedia.org/wiki/Request_for_Comments>`_ to demonstrate what a scraper using **spatula** looks like.

After reading through this you can continue on to the tutorial or look at more detailed documentation on **spatula**'s API. (TODO)

Installation
------------

**spatula** is on PyPI, and can be installed via any standard package management tool::

  poetry add spatula

or::

  pip install spatula


Scraping a Single Page
----------------------

RFCs live on pages like `RFC 1945 <https://tools.ietf.org/html/rfc1945>`_.

We're going to pull some data elements from the page that look like::

  <meta name="DC.Creator" content="Nielsen, Henrik Frystyk" />
  <meta name="DC.Creator" content="Berners-Lee, Tim" />
  <meta name="DC.Creator" content="Fielding, Roy T." />
  <meta name="DC.Date.Issued" content="May, 1996" />
  <meta name="DC.Title" content="Hypertext Transfer Protocol -- HTTP/1.0" />

To demonstrate extracting the title & authors from special `<meta>` elements, we'll write a small class to handle individual pages.

To do so we subclass :py:class:`HtmlPage`, and override the :py:meth:`process_page` function.

Example::

  # imports we'll use in this example
  from spatula import (
      HtmlPage, HtmlListPage, CSS, SimilarLink, Workflow
  )


  class RFC(HtmlPage):
      def process_page(self):
          title_elem = CSS("meta[name='DC.Title']").match_one(self.root)
          return dict(
              title=title_elem.get("content"),
              authors=[
                e.get("content")
                for e in CSS("meta[name='DC.Creator']").match(self.root)
              ]
          )


This will extract the title and authors elements from the page.

It can be tested from the command line like::

  $ spatula test example.RFC --source "https://tools.ietf.org/html/rfc1945"
  fetching https://tools.ietf.org/html/rfc1945 for RFC
  {'authors': ['Nielsen, Henrik Frystyk', 'Berners-Lee, Tim', 'Fielding, Roy T.'],
   'title': 'Hypertext Transfer Protocol -- HTTP/1.0'}


Scraping a List Page
--------------------

It is fairly common for a scrape to encounter some sort of directory or listing page.

**spatula** provides a special interface for these cases.
See below how we process each matching link by deriving from a :py:class:`HtmlListPage` and providing a :py:attr:`selector` as well as a :py:meth:`process_item` method.

Example::


  class RFCList(HtmlListPage):
      # by providing this here, it can be omitted on the command line
      # useful in cases where the scraper is only meant for one page
      source = "https://tools.ietf.org/rfc/"

      # for this demo we just want to get the one digit RFCs
      selector = SimilarLink(r"http://tools.ietf.org/html/\d$")

      def process_item(self, item):
          return dict(url=item.get("href"))

This will extract all links on the page in the format specified by the given regular expression.
It can be tested from the command line like::

  $ spatula test example.RFCList
  fetching https://tools.ietf.org/rfc/ for RFCList
  0: {'url': 'http://tools.ietf.org/html/1'}
  1: {'url': 'http://tools.ietf.org/html/2'}
  ...
  8: {'url': 'http://tools.ietf.org/html/9'}


Defining a Simple Workflow
--------------------------

Notice that :py:class:`RFCList` returns URLs, and we need to instantiate :py:class:`RFC` with a source on the command line.

We can chain these together into what we'll call a :py:class:`Workflow`, like so::

  class RFC(HtmlPage):
    ...
    # add this method to RFC
    # it is called if no source is provided to determine the URL to
    # scrape, it will be getting the output from RFCList as self.input
    def get_source_from_input(self):
        return self.input["url"]

  ...

  # this line added at the bottom of the file, defines a workflow
  rfc_details = Workflow(RFCList(), RFC)

Running a workflow will write the output as JSON (or a format of your selection) to disk.

Doing so looks like::

  $ poetry run spatula scrape example.rfc_details
  fetching http://tools.ietf.org/html/2 for RFC
  fetching http://tools.ietf.org/html/3 for RFC
  fetching http://tools.ietf.org/html/4 for RFC
  fetching http://tools.ietf.org/html/5 for RFC
  fetching http://tools.ietf.org/html/6 for RFC
  fetching http://tools.ietf.org/html/7 for RFC
  fetching http://tools.ietf.org/html/8 for RFC
  ...
  scrapelib.HTTPError: 404 while retrieving https://tools.ietf.org/html/8

Oops, a bad link!  

Handling Errors
---------------

In this case, the site has a bad link.

We need to tell spatula that it is OK to skip an item that has a bad link.

We'll add to :py:class:`RFC`::

  class RFC(HtmlPage):
    ...

    def handle_error_response(self, exception):
        # TODO: use logging
        print("skipping", self.source.url)

Wrapping Up
-----------

Let's try to run the scrape again::

  $ poetry run spatula scrape example.rfc_details
  fetching http://tools.ietf.org/html/8 for RFC
  skipping http://tools.ietf.org/html/8
  fetching http://tools.ietf.org/html/9 for RFC
  skipping http://tools.ietf.org/html/9
  success: wrote 7 objects to _scrapes/2021-01-18/001


And now our scraped data is on disk, ready for you to use.
