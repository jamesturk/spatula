# spatula (next-gen scrape) 2.0

## Motivations

- Scrapers should be easy to write and understand.
- It should be possible to scrape a single item for incremental scraping and testing during development.
- To this end, providing an interface that makes this not only possible, but makes the opposite harder, seems like a good idea.

## Observations

There are four types of pages we generally encounter:

- 'Listing' pages (e.g. a list of all legislators in a chamber or all bills in a session)
  - Note: Sometimes these are paginated.
- 'Detail' pages (e.g. a page with a person's biographical information or a bill's status updates and relevant links)
- 'Auxiliary Detail' pages that augment detail information (e.g. a list of versions loaded from a separate page)
- 'Augmentation' pages that provide data that complements the entire data set.  (e.g. a page mapping bills to their subjects, often scraped first and stored in a dictionary that is referenced by each bill as it is scraped)

## Philosophy

Generally speaking, we want to enforce some best practices by making it easiest to do the right thing.

So combining our motivations & observations, arriving at:

- One class or function per type of page.
- Listing Pages are responsible for returning a list of things to get details on. (and nearly nothing else, see question #2)
- Detail pages are responsible for returning built objects (i.e. Person, Bill, etc.) that are as complete as possible.
- Detail pages can call auxiliary page scrapers as needed.  These classes simply return dictionaries of data to add.
- Augmentation pages can provide data that will be grafted onto the entire data set, but should be used sparingly.

## Example

Let's say a hypothetical state has the following pages:

- listing of all senators
- listing of all reps
  - all people happen to use nearly identical pages regardless of chamber
- list of all bills (possibly paginated?)
  - detail page for a given bill
    - detail page for a given vote, linked from bills (0 or more per bill)
- another separate page that lists all bill ids for current session under given subjects (information not available on bill pages)

We'd go about writing this by writing individual classes, perhaps:

- SenateRoster - listing of all senators
- HouseRoster - listing of all reps
- PersonDetail - all people happen to use nearly identical pages regardless of chamber
- BillList - list of all bills (possibly paginated?)
- BillDetail - detail page for a given bill
- VoteDetail - detail page for a given vote, linked from bills (0 or more per bill)
- SubjectListing - aux. page that lists all bill ids for current session under given subjects

## Proposed API

`Page.set_raw_data`: generally preprocesses fetched remote data (e.g. parses HTML or CSV).  Most scrapers will use a Page subclass like HtmlPage and not need to implement their own version of this. (see scraper/fetch separation below for more thoughts)

`Page.process_page`: function that will convert the raw data into an object of the desired type (Person, Bill, or perhaps a list or dictionary for supplemental pages)

And two important conventions:
* `ListPage` type classes should return (yield?) lists of dictionaries that have 'url' keys.
* `DetailPage` type classes are responsible for yielding complete objects.

TODO: explain how Aux. Detail pages work (yielding dictionaries, lists, etc.)

This lets us define a very simple `Workflow` class:

```
# e.g.
senate_members = Workflow(
    PersonList("http://mgaleg.maryland.gov/mgawebsite/Members/Index/senate"), PersonDetail
)
```

This workflow can then be invoked from the command line, which will call `PersonDetail.process_page` on every page yielded by `PersonList.process_page`.

In a sense, that's it.  A scraper that uses an API or bulk data might only need these.  We can also add some helpers, like `HtmlListPage` that handles common use cases:

`HtmlListPage.selector`: define a selector (see Selectors below)
`HtmlListPage.process_item`: function to process each item yielded by applying selector to the HTML

For examples of this, ``ok.py`` and ``md.py`` have been written in this style.

## Additional Features

Two other ideas have been incorporated into the current version.  Neither is strictly necessary, but fit the general framework nicely.

### Scraper / Fetch Separation

Why don't page objects fetch themselves?  A big part of this is that we want to share a scraper among them for rate limiting and other configuration.  In theory this could mean that each one is instantiated with a scraper parameter, but that'd be a bit more cumbersome.  So instead, Page has the `set_raw_data` function.  This could make testing even easier, as there's no need to mock HTTP requests/etc. at some point.  

That said, it is a bit odd, and I'm open to rethinking it (the design used to rely on Scraper to do a lot more, which justified this even more, but that's been dialed back).  I'm not sure in practice though most scraper authors will notice, as `set_raw_data` isn't ever called in user-facing code.

### Selectors

While playing with ideas for `HtmlListPage` I originally had `HtmlListPage.xpath` which was an XPath that was applied, with the results being fed to `process_item`.  I realized that there are other cases that might be useful, CSS selectors, something to just look for links matching a pattern, etc.

By wrapping all of these in a new `Selector` interface as you can see in selectors.py, we can also encourage better error checking.  Note how ok.py uses `num_items=48` and `num_items=101` to protect itself against weird page changes that could result in issues later.

## Proposed Usage

While developing, the following commands are available (spatula is the stand-in name for the CLI entrypoint):

`spatula test md.SenateRoster` - Will print a list of all data yielded from the SenateRoster page.

`spatula test md.PersonDetail https://example.com/123` - Will print result of using PersonDetail scraper on given URL.

`spatula run md.house_members_workflow` - Will run a defined 'Workflow' which is a configuration of an entrypoint.  Details TBD.


## Open Questions

1. How do we want to handle pagination?  This is a special case where a list scraper should do multiple fetches.

2. Should listing pages be able to hand additional information to detail pages they invoke?  There are cases where it is hard (impossible?) to get certain information on a detail page but easy from the listing.  (Example is chamber information in Maryland legislators.)

3. How do augmentation pages work?  Should this happen magically or should the user be required to map aux. data to bills as happens now?

4. What edge cases are we aware of that seem hard to implement in this structure? 

5. Lots of things aren't named very well yet as concepts evolve. Clearer names are more than welcome.

## Things Not Handled Here

This interface is by design, object-agnostic.  I also have a basic `Person` object in common.py, but that'd be kept separate from the actual scraping interface.  That, I believe, is the correct place to do things like clean up dates/etc.  and is best treated as a separate problem.  Plenty of improvements to make there too, but mostly unrelated to this work.

This is designed to write JSON/YAML/etc. to disk, all import logic is separate.
