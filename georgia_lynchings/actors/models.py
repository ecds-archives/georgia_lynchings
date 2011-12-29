from georgia_lynchings.events.rdfns import dcx
from georgia_lynchings.events.sparqlstore import SparqlStore
import logging

logger = logging.getLogger(__name__)

class Actor(object):
    '''An Actor is an object type defined by the project's (currently
    private) PC-ACE database. It represents a participant in a lynching 
    event and all of the events associated with it.
    '''

    def __init__(self, id):
        self.uri = dcx['r' + str(id)]

    def uri_as_ntriples(self):
        '''Encode object URI as an `N-Triples
        <http://www.w3.org/2001/sw/RDFCore/ntriples/>`_ URIRef for use in
        SPARQL initial bindings.'''
        # TODO: Properly escape the URI. For now we conveniently limit
        # ourselves to URIs that don't need encoding.
        return '<%s>' % (self.uri,)

    def get_macroevents(self):
        '''Get all macro events associated with this actor/participant.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `individual`: the data_Complex Indentifier
                  
                It retrieves the following data:
                  * `triplet`: the Semantic Triplet of an event for actor/participant
                  * `role`: either subject(Participant-S) or object(Participant-O)
                  * `trlabel`: the triplet label
                  * `event`: the uri of the event associated with this article
                  * `evlabel`: the event label
                  * `macro`: the uri of the associated macro event
                  * `melabel`: the macro event label
        '''
        logger.debug("actors get_macroevents %s" % self.uri_as_ntriples())
        query='''
        PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
        PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
        SELECT ?actorlabel ?triplet ?role ?trlabel ?event ?evlabel ?macro ?melabel 
        WHERE {
          ?individual ^sxcxcx:r31 ?actor;
                dcx:Identifier ?actorlabel.
          {
            ?actor ^sxcxcx:r30 ?participant. 
            ?triplet sxcxcx:r63 ?participant. 
            BIND("subject" as ?role)
          } UNION {
            ?actor ^sxcxcx:r35 ?participant.  
            ?triplet sxcxcx:r65 ?participant.  
            BIND("object" as ?role)
          } 

          ?triplet dcx:Identifier ?trlabel.
          ?event sxcxcx:r62 ?triplet;       
                 dcx:Identifier ?evlabel.
          ?macro sxcxcx:r61 ?event;          
                 dcx:Identifier ?melabel.      
        }
        '''
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'individual': self.uri_as_ntriples()}) 
        # return the dictionary resultset of the query          
        return resultSet
