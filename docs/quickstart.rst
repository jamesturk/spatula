Quickstart
==========

This guide contains quick examples of how you could scrape a small list of `RFCs <https://en.wikipedia.org/wiki/Request_for_Comments>`_ to demonstrate what it looks like to write a scraper using **spatula**.

You can skip ahead if you want to read about **spatula**'s :ref:`Design Philosophy`,
or check out the :ref:`Tutorial` or :ref:`API Reference`.

Installation
------------

**spatula** is on PyPI, and can be installed via any standard package management tool::

  poetry add spatula

or::

  pip install spatula


Scraping a Single Page
----------------------

RFCs live on pages like `RFC 1945 <https://tools.ietf.org/html/rfc1945>`_.

We're going to pull some data elements from the page that look like:

.. code-block:: html

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

It can be tested from the command line like:

.. code-block:: console

  $ spatula test example.RFC --source "https://tools.ietf.org/html/rfc1945"
  INFO:rfc.RFC:fetching https://tools.ietf.org/html/rfc1945
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
          return item.get("href")

This will extract all links on the page in the format specified by the given regular expression.
It can be tested from the command line like:

.. code-block:: console

  $ spatula test example.RFCList
  INFO:rfc.RFCList:fetching https://tools.ietf.org/rfc/
  1: http://tools.ietf.org/html/1
  2: http://tools.ietf.org/html/2
  ...
  9: http://tools.ietf.org/html/9


Chaining Pages Together
-----------------------

Notice that :py:class:`RFCList` returns URLs, and we need to instantiate :py:class:`RFC` with a source on the command line.

We can chain these together by having :py:class:`RFCList` return instances of :py:class:`RFC`,
which will tell *spatula* more work is needed.

.. code-block:: python
  :emphasize-lines: 9-10

  class RFCList(HtmlListPage):
      # by providing this here, it can be omitted on the command line
      # useful in cases where the scraper is only meant for one page
      source = "https://tools.ietf.org/rfc/"

      # for this demo we just want to get the one digit RFCs
      selector = SimilarLink(r"http://tools.ietf.org/html/\d$")

      def process_item(self, item):
          return RFC(source=item.get("href"))

Now a run looks like:

.. code-block:: console

  $ spatula test example.RFCList
  INFO:rfc.RFCList:fetching https://tools.ietf.org/rfc/
  1: RFC(source=http://tools.ietf.org/html/1)
  2: RFC(source=http://tools.ietf.org/html/2)
  ...
  9: RFC(source=http://tools.ietf.org/html/9)
 

By default, ``spatula test`` just shows the result of the page you're working on.

Running a Scrape
----------------

Now that we're happy with our individual pages, we might want to have the data output to disk.

For this we use the ``spatula scrape`` command:

.. code-block:: console

  $ spatula scrape example.RFCList
  INFO:rfc.RFCList:fetching https://tools.ietf.org/rfc/
  INFO:rfc.RFC:fetching http://tools.ietf.org/html/1
  INFO:rfc.RFC:fetching http://tools.ietf.org/html/2
  ...
  scrapelib.HTTPError: 404 while retrieving https://tools.ietf.org/html/8

Oops, a bad link!

Handling Errors
---------------

In this case, the site has a bad link.

We need to tell spatula that it is OK to skip an item that has a bad link.

We'll add to :py:class:`RFC`:

.. code-block:: python
  :emphasize-lines: 4-6

  class RFC(HtmlPage):
    ...

    def process_error_response(self, exception):
        # self.logger is configured for you already on all Page classes
        self.logger.warning(f"skipping {self.source.url}")

Wrapping Up
-----------

Let's try to run the scrape again:

.. code-block:: console

  $ spatula scrape example.rfc_details
  ...
  INFO:rfc.RFC:fetching http://tools.ietf.org/html/8
  WARNING:rfc.RFC:skipping http://tools.ietf.org/html/8
  INFO:rfc.RFC:fetching http://tools.ietf.org/html/9
  WARNING:rfc.RFC:skipping http://tools.ietf.org/html/9
  success: wrote 7 objects to _scrapes/2021-02-01/001


And now our scraped data is on disk, ready for you to use.

You might want to read a bit more about **spatula**'s :ref:`Design Philosophy`,
or check out the :ref:`Tutorial` or :ref:`API Reference`.
