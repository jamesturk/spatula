Quickstart
==========

Installation
------------

**spatula** is on PyPI, and can be installed via any standard package management tool::

  poetry add spatula

or::

  pip install spatula


Scraping a Single Page
----------------------

Example::

  from spatula.pages import HtmlPage
  from spatula.selectors import CSS


  class RFC(HtmlPage):
      def process_page(self):
          return dict(
              title=CSS("meta[name='DC.Title']").match_one(self.root).get("content"),
              authors=[e.get("content") for e in CSS("meta[name='DC.Creator']").match(self.root)]
          )

This will extract the title and authors elements from an RFC (TODO: link)
It can be tested from the command line like::

  $ spatula test example.RFC --source "https://tools.ietf.org/html/rfc1945"
  fetching https://tools.ietf.org/html/rfc1945 for RFC
  {'authors': ['Nielsen, Henrik Frystyk', 'Berners-Lee, Tim', 'Fielding, Roy T.'],
   'title': 'Hypertext Transfer Protocol -- HTTP/1.0'}


Scraping a List Page
--------------------

Example::

  from spatula.pages import HtmlListPage
  from spatula.selectors import SimilarLink


  class RFCList(HtmlListPage):
      source = "https://tools.ietf.org/rfc/"
      # for this demo we just want to get the one digit RFCs
      selector = SimilarLink(r"http://tools.ietf.org/html/\d$") 
      def process_item(self, item):
          return dict(url=item.get("href"))

This will extract all links on the page in the format specified by the given regular expression.
It can be tested from the command line like::

  $ spatula test example.RFCList 
  fetching https://tools.ietf.org/rfc/ for RFCList
  0: {'url': 'http://tools.ietf.org/html/1119'}
  1: {'url': 'http://tools.ietf.org/html/2026'}
  2: {'url': 'http://tools.ietf.org/html/1'}
  ...
  9395: {'url': 'http://tools.ietf.org/html/8971'}
  9396: {'url': 'http://tools.ietf.org/html/8973'}


Defining a Simple Workflow
--------------------------

Notice that :py:class:`RFCList` returns URLs, and we need to instantiate :py:class:`RFC` with a source on the command line.

We can chain these together into what we'll call a :py:class:`Workflow`, like so::

  from spatula.core import Workflow 

  class RFC(HtmlPage):
    ... 
    # add this method to RFC
    def get_source_from_input(self):
        return self.input["url"]

  # add this line at the bottom of the file
  rfc_details = Workflow(RFCList(), RFC)

And then run this workflow::

  poetry run spatula scrape example.rfc_details

This will write the output as JSON in a directory printed to the command line.
