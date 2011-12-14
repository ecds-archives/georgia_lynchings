import logging
from django.db import models
from georgia_lynchings.events.rdfns import dcx
from georgia_lynchings.events.sparqlstore import SparqlStore

logger = logging.getLogger(__name__)

class Event(object):
    
    def __init__(self):
        logger.debug("Event begin")
    
    def get_articles(self, row_id=None):
        "Get articles for event."
        '''
        row_id: macro event id, format 12
        '''         
        logger.debug("get_articles for row = [%s]\n" % row_id)
        query='''
        PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
        PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
        PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
        PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
        PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
        SELECT DISTINCT ?melabel ?event ?evlabel ?dd ?docpath 
        WHERE {
          ?macro a scx:r1;
                 dcx:Identifier ?melabel;
                 sxcxcx:r61 ?event.
          ?event dcx:Identifier ?evlabel.

          ?dxcxd dxcxd:Complex ?event;
                 dxcxd:Document ?dd.
          ?dd ssx:r85 ?docpath. 
        } 
        ORDER BY ?event ?docpath
        '''
        # a SPARQL representation of the URI of the macro event we want, for
        # initial query bindings
        macro_uri_rep = '<%s>' % (dcx['r' + row_id],)
        # Post the query       
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': macro_uri_rep}) 
        # return the dictionary resultset of the query          
        return resultSet
