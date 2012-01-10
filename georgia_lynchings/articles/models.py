from urllib import quote
from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.sparqlstore import SparqlStore
from georgia_lynchings import query_bank
import logging

logger = logging.getLogger(__name__)


def all_articles():
    '''Get all articles associated with this macro event, along with the
    particular events that the articles are attached to.

    :rtype: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:

              * `melabel`: the :class:`MacroEvent` label
              * `event`: the uri of the event associated with this article
              * `evlabel`: the event label
              * `dd`: the uri of the article
              * `docpath`: a relative path to the document data

            The matches are ordered by `event` and `docpath`.
    '''

    query=query_bank.articles['all']
    ss=SparqlStore()
    resultSet = ss.query(sparql_query=query)
    if resultSet: logger.debug("\nLength of resultSet = [%d]\n" % len(resultSet))
    else: logger.debug("\nResultSet is empty.\n")
    for result in resultSet:
        # Clean up data, add "n/a" if value does not exist
        if 'docpath' not in result: result['docpath'] = 'n/a'
        else: 
            result['docpath_link'] = quote(result['docpath'].replace('\\', '/'))
            result['docpath'] = result['docpath'][10:] 
        if 'papername' not in result: result['papername'] = 'n/a'
        if 'paperdate' not in result: result['paperdate'] = 'n/a'
        if 'articlepage' not in result: result['articlepage'] = 'n/a'
    # return the dictionary resultset of the query          
    return resultSet
