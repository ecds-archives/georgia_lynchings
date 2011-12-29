from georgia_lynchings.events.rdfns import dcx, scx, ssx, sxcxcx
from georgia_lynchings.events.sparqlstore import SparqlStore
from pprint import pprint
from urllib import quote
import logging

logger = logging.getLogger(__name__)

class NewspaperArticles(object):

    def all_articles(self):
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
        logger.debug("articles all_articles")
        query='''
            prefix dd: <http://galyn.example.com/source_data_files/data_Document.csv#>
            prefix ssx: <http://galyn.example.com/source_data_files/setup_Simplex.csv#>

            select ?id ?paperdate ?papername ?articlepage ?docpath where {
            ?dd a dd:Row;
                dd:ID ?id.
            optional { ?dd ssx:r68 ?paperdate }
            optional { ?dd ssx:r69 ?papername }
            optional { ?dd ssx:r73 ?articlepage }
            optional { ?dd ssx:r85 ?docpath }
            }
        '''
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query)
        if resultSet: logger.debug("\nLength of resultSet = [%d]\n" % len(resultSet))
        else: logger.debug("\nResultSet is empty.\n")
        for result in resultSet:
            # Clean up data, add "n/a" if value does not exist
            if not result.has_key('docpath'): result.update({'docpath':{'value':'n/a'}})            
            else: 
                result['docpath_link'] = quote(result['docpath']['value'].replace('\\', '/'))
                result['docpath']['value'] = result['docpath']['value'][10:] 
            if not result.has_key('papername'): result.update({'papername':{'value':'n/a'}})
            if not result.has_key('paperdate'): result.update({'paperdate':{'value':'n/a'}})
            if not result.has_key('articlepage'): result.update({'articlepage':{'value':'n/a'}})                                         
        # return the dictionary resultset of the query          
        return resultSet
