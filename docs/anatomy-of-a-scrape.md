# Anatomy of a Scrape

This diagram illustrates the control flow when `Page.do_scrape` is invoked programmatically or via `spatula scrape`:

[![](https://mermaid.ink/img/eyJjb2RlIjoiZmxvd2NoYXJ0IFREXG4gICAgICAgIERFUFtzY3JhcGUgYW55IGRlcGVuZGVuY2llc10gLS0-IFExXG4gICAgICAgIFExe2RvZXMgUGFnZSBoYXZlIGEgc291cmNlP31cbiAgICAgICAgUTEgLS0geWVzIC0tPiBHUlxuICAgICAgICBRMSAtLSBubyAtLT4gU0ZJW1twYWdlLmdldF9zb3VyY2VfZnJvbV9pbnB1dF1dXG4gICAgICAgIFNGSSAtLT4gR1JcbiAgICAgICAgU0ZJIC0uIG5vdCBwcm92aWRlZCAuLT4gRUUoW2V4aXQgd2l0aCBlcnJvcl0pXG4gICAgICAgIEdSW1tzb3VyY2UuZ2V0X3Jlc3BvbnNlXV0gLS0gc3VjY2Vzcywgc2VsZi5yZXNwb25zZSBpcyBub3cgc2V0IC0tPiBQUFJbW3BhZ2UucG9zdHByb2Nlc3NfcmVzcG9uc2VdXVxuICAgICAgICBHUiAtLiBleGNlcHRpb24gLi0-IFBFUltbcGFnZS5wcm9jZXNzX2Vycm9yX3Jlc3BvbnNlXV1cbiAgICAgICAgUEVSIC0uIHJhaXNlcyBleGNlcHRpb24gLi0-IEVFMihbZXhpdCB3aXRoIGVycm9yXSlcbiAgICAgICAgUEVSIC0tPiBHTlNcbiAgICAgICAgUFBSIC0tPiBQUFtbcGFnZS5wcm9jZXNzX3BhZ2VdXVxuICAgICAgICBQUCAtLSB5aWVsZHMgb3IgcmV0dXJucyBQYWdlIG9iamVjdCAtLT4gU1Bbc2NyYXBlIHN1YnBhZ2VzXVxuICAgICAgICBTUCAtLT4gR05TXG4gICAgICAgIFBQIC0tPiBHTlNbW3BhZ2UuZ2V0X25leHRfc291cmNlXV1cbiAgICAgICAgR05TIC0tPiBHUlxuICAgICAgICBHTlMgLS4gbm8gbmV4dCBzb3VyY2UgLi0-IERPTkUoW2RvbmVdKSIsIm1lcm1haWQiOnsidGhlbWUiOiJmb3Jlc3QifSwidXBkYXRlRWRpdG9yIjpmYWxzZSwiYXV0b1N5bmMiOnRydWUsInVwZGF0ZURpYWdyYW0iOmZhbHNlfQ)](https://mermaid-js.github.io/mermaid-live-editor/edit/##eyJjb2RlIjoiZmxvd2NoYXJ0IFREXG4gICAgICAgIERFUFtzY3JhcGUgYW55IGRlcGVuZGVuY2llc10gLS0-IFExXG4gICAgICAgIFExe2RvZXMgUGFnZSBoYXZlIGEgc291cmNlP31cbiAgICAgICAgUTEgLS0geWVzIC0tPiBHUlxuICAgICAgICBRMSAtLSBubyAtLT4gU0ZJW1twYWdlLmdldF9zb3VyY2VfZnJvbV9pbnB1dF1dXG4gICAgICAgIFNGSSAtLT4gR1JcbiAgICAgICAgU0ZJIC0uIG5vdCBwcm92aWRlZCAuLT4gRUUoW2V4aXQgd2l0aCBlcnJvcl0pXG4gICAgICAgIEdSW1tzb3VyY2UuZ2V0X3Jlc3BvbnNlXV0gLS0gc3VjY2Vzcywgc2VsZi5yZXNwb25zZSBpcyBub3cgc2V0IC0tPiBQUFJbW3BhZ2UucG9zdHByb2Nlc3NfcmVzcG9uc2VdXVxuICAgICAgICBHUiAtLiBleGNlcHRpb24gLi0-IFBFUltbcGFnZS5wcm9jZXNzX2Vycm9yX3Jlc3BvbnNlXV1cbiAgICAgICAgUEVSIC0uIHJhaXNlcyBleGNlcHRpb24gLi0-IEVFMihbZXhpdCB3aXRoIGVycm9yXSlcbiAgICAgICAgUEVSIC0tPiBHTlNcbiAgICAgICAgUFBSIC0tPiBQUFtbcGFnZS5wcm9jZXNzX3BhZ2VdXVxuICAgICAgICBQUCAtLSB5aWVsZHMgb3IgcmV0dXJucyBQYWdlIG9iamVjdCAtLT4gU1Bbc2NyYXBlIHN1YnBhZ2VzXVxuICAgICAgICBTUCAtLT4gR05TXG4gICAgICAgIFBQIC0tPiBHTlNbW3BhZ2UuZ2V0X25leHRfc291cmNlXV1cbiAgICAgICAgR05TIC0tPiBHUlxuICAgICAgICBHTlMgLS4gbm8gbmV4dCBzb3VyY2UgLi0-IERPTkUoW2RvbmVdKVxuIiwibWVybWFpZCI6IntcbiAgXCJ0aGVtZVwiOiBcImZvcmVzdFwiXG59IiwidXBkYXRlRWRpdG9yIjpmYWxzZSwiYXV0b1N5bmMiOnRydWUsInVwZGF0ZURpYWdyYW0iOmZhbHNlfQ)


## Dependencies

When a scrape is initiated, the first thing *spatula* will do is examine any dependencies declared on the page being invoked.

Each dependency is resolved (in essence a full scrape of its own) with the resulting data saved to an internal cache (to avoid duplicating scrapes of shared dependencies).

See [Specifying Dependencies](advanced-techniques.md#specifying-dependencies) for a practical application.

## Ensuring a Source Exists

Once any dependencies are resolved, the page attempts to resolve a `source` attribute.

There are a number of places that a `source` might come from, in order of precedence:

0. overridden using the `--source` parameter if using a CLI scrape
0. passed in via class constructor (e.g. if this is a subpage)
0. set as a class attribute ([`Page.source`](reference.md#page))
0. retrieved via [`get_source_from_input`](reference.md#spatula.pages.Page.get_source_from_input)

!!! note
    If any of these methods return a string, it will be automatically converted to a [`URL`](reference.md#url).

## Processing the Response

Once a `source` is obtained, `source.get_response` is called, which typically means an HTTP request is performed.

If an exception is raised, it will be passed to [`process_error_response`](reference.md#spatula.pages.Page.process_error_response).

If all goes well, the `response` attribute of the page class is set and [`postprocess_response`](reference.md#spatula.pages.Page.postprocess_response) will be called.  This is where classes like `HtmlPage` and `CsvListPage` process the `response` and do any additional parsing required.

## User Code: Processing Page Contents

Once the response has been processed, *spatula* will call the page's `process_page` method.

In a standard use of *spatula* this is the first time that user-written code is run.

`process_page` can return or yield actual data, or additional pages to continue the scrape.

### Handling Subpages

If subpages are returned, each of them will be handled in essentially the same cycle.

## Pagination

After `process_page` terminates, *spatula* checks if there is a result from [`get_next_source`](reference.md#spatula.pages.Page.get_next_source).

If so, a new instance of the page class is instantiated with the new `source` set & the process is repeated from [processing the response](#processing-the-response).
