## "Spatula"

An experiment in making scrapers easier to maintain and semi-testable.

General premise is that scraping is broken down into page-by-page tasks.

Each type of page encountered by the scraper is represented by a subclass of
`Page`

99% of scraper code either goes in handle\_list\_item (for cases where
list of similar objects is being scraped, like a table) or in
handle\_page if a similar item is being scraped.

So if there were a list of legislators and a detail page for each one might
make LegislatorList and LegislatorDetail classes.

LegislatorList could likely get by with just handle\_list\_item overridden.

LegislatorDetail likely with just handle\_page.

Usage looks something like:

    yield from scraper.scrape_page_items(LegislatorList)

And within LegislatorList.handle\_list\_item something similar to:

    self.scrape_page(LegislatorDetail, url=legislator_url, obj=leg)


A few notes:

- ``url`` can either be passed in to scrape_page/scrape_page_items or set on the class itself in cases where it is static (like list pages).

- the ``obj`` parameter allows a partially-completed object to be filled out by a detail page

- Additional parameters can be passed into the scrape\_\* methods and will be available as extras.
    (TODO: should these chain?  refine API for accessing these beyond kwargs.get?)
