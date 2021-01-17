

Planning A Scrape
-----------------

Let's say a hypothetical state had the following distinct types of pages:

* Listing of all State Senators
* Listing of all State Representatives (for our purposes let's say this page doesn't have much in common with the senage page, and is paginated)
* Contact information page for each member, each of which seems to use the same underlying template.
* A separate page that is a directory of photographs for all members.

(TODO: add example of aux detail page)

Based on this structure, we'd wind up writing four classes to handle the four distinct types:

* :py:class:`SenateRoster` - this will scrape the list of senators, including links to their detail pages
* :py:class:`HouseRoster` - this will scrape the list of representatives, note that pagination will be handled here
* :py:class:`PersonDetail` - this will gather the contact information
* :py:class:`PhotoAugmentation` - this will gather the photo URLs associated with member names so that we can associate the photo with the other information we've gathered

Once we have that plan, we can begin working on these four components almost entirely in isolation of one another.  While working on any of these classes, spatula provides ways to get rapid feedback on how your :py:class:`Page` subclasses are handling any given page you want to try them on.  This means you can work with the :py:class:`PersonDetail` scraper first, before having a functioning :py:class:`SenateRoster` scraper, but you don't need to write extra boilerplate code that will be removed later.  

Once you're satisfied with how individual components are working, you'll wire them together with a :py:class:`Workflow` that'll provide an entrypoint that perhaps starts with the :py:class:`HouseRoster`, fetches the :py:class:`PhotoAugmentation` page, and then uses the :py:class:`PersonDetail` to get each representative's contact information, yielding a single object per legislator that'll be written to disk in a format of your choice.
