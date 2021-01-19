API Reference
=============

.. module:: spatula

Pages
-----

.. py:class:: Page

  Base class for all **Page** objects.

  .. py:attribute:: source

    Can be set on subclasses of :py:class:`Page` to define the initial HTTP
    request that the page will handle in its :py:meth:`process_response`.

    For simple GET requests, :py:data:`source` can be a string.
    :py:class:`URL` should be used for more advanced use cases.

  .. py:attribute:: response

    Provides access to the raw :py:class:`requests.Response` object obtained
    by fetching py:data:`source`.

  .. automethod:: Page.postprocess_response
  .. automethod:: Page.process_error_response
  .. automethod:: Page.process_page

.. py:class:: HtmlPage

  .. inheritance-diagram:: HtmlPage

  Page that automatically handles parsing and normalizing links in an HTML response.

  **Provided Variables:**

  .. py:attribute:: root

    :py:class:`lxml.etree.Element` object representing the root element (e.g. ``<html>``) on the page.

    Can use the normal lxml methods (such as :py:meth:`cssselect` and :py:meth:`getchildren`), or
    use this element as the target of a :py:class:`Selector` subclass.

.. py:class:: JsonPage

  .. inheritance-diagram:: JsonPage

  Page that automatically handles parsing a JSON response.

  **Provided Variables:**

  .. py:attribute:: data

    Parsed JSON response data.

.. py:class:: XmlPage

  .. inheritance-diagram:: XmlPage

  Page that automatically handles parsing and normalizing links in an XML response.

  **Provided Variables:**

  .. py:attribute:: root

    :py:class:`lxml.etree.Element` object representing the root XML element on the page.

    Can use the normal lxml methods (such as :py:meth:`xpath` and :py:meth:`getchildren`), or
    use this element as the target of a :py:class:`Selector` subclass.

.. py:class:: ListPage

  .. inheritance-diagram:: ListPage

  Base class for common pattern of extracting many homogenous items from one page.

  Instead of overriding :py:meth:`process_response`, subclasses should provide a :py:meth:`process_item` that will be invoked on each subitem in the page (as defined by the particular subclass being used).

.. py:class:: CsvListPage

  .. inheritance-diagram:: CsvListPage

  :py:class:`ListPage` subclass where each row of a CSV file will be handed to :py:meth:`process_item`.

.. py:class:: HtmlListPage

  .. inheritance-diagram:: HtmlListPage

  :py:class:`ListPage` subclass where each element matching the provided :py:attr:`selector` will be handed to :py:meth:`process_item`.

.. py:class:: JsonListPage

  .. inheritance-diagram:: JsonListPage

  :py:class:`ListPage` subclass where each element in a JSON list response will be handed to :py:meth:`process_item`.

.. py:class:: XmlListPage

  .. inheritance-diagram:: XmlListPage

  :py:class:`ListPage` subclass where each element matching the provided :py:attr:`selector` will be handed to :py:meth:`process_item`.  Unlike :py:class:`HtmlListPage`, the root element will be parsed with the `lxml.etree` parser.

Selectors
---------

.. autoclass:: Selector
  :members:


.. autoclass:: CSS


.. autoclass:: SimilarLink


.. autoclass:: XPath

Sources
-------

.. autoclass:: URL

.. autoclass:: NullSource


Workflows
---------

.. autoclass:: Workflow
