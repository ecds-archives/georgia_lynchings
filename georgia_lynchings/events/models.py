from georgia_lynchings.events.rdfns import dcx, scx, ssx, sxcxcx
from georgia_lynchings.events.sparqlstore import SparqlStore

class MacroEvent(object):
    '''A Macro Event is an object type defined by the project's (currently
    private) PC-ACE database. It represents a lynching case and all of the
    individual events associated with it.
    '''

    # RDF relationships: We expect future code will use the below
    # relationships to make it easier to generate SPARQL queries and other
    # graph traversals from idiomatic Python code. That code doesn't exist
    # yet, so for now these properties serve more as handy documentation of
    # common RDF properties on MacroEvent objects

    # NOTE: Many of these relationships are defined in the private PC-ACE
    # database for this project. The URIs were found a priori by examining
    # the RDF data imported from the database setup tables.

    rdf_type = scx.r1
    'the URI of the RDF Class describing macro event objects'

    # Every PC-ACE complex object has a label. TODO: Consider extracting a
    # parent class to reflect this?
    label = dcx.Identifier
    'a human-readable label for this macro event'

    # complex fields potentially attached to a MacroEvent
    events = sxcxcx.r61
    'the events associated with this macro event'

    # simplex fields potentially attached to a MacroEvent
    county = ssx.r18
    'the county in which the lynching occurred'
    victim = ssx.r82
    'the victim of the lynching'
    case_number = ssx.r84
    'a case number identifying this lynching case'
    verified_semantic = ssx.r89
    '''has the coded data for this case been manually reviewed for semantic
    consistency?'''
    verified_details = ssx.r90
    '''has the coded data for this case been manually reviewed for detail
    accuracy?'''
    last_coded = ssx.r94
    'the date this case most recently had coding data added'

    # methods for wrapping a MacroEvent around a URI and querying utility
    # data about it. For now these methods have hard-coded SPARQL, but we
    # hope in time to be able to generate these queries from the RDF
    # properties above.

    def __init__(self, id):
        self.uri = dcx['r' + str(id)]

    def uri_as_ntriples(self):
        '''Encode object URI as an `N-Triples
        <http://www.w3.org/2001/sw/RDFCore/ntriples/>`_ URIRef for use in
        SPARQL initial bindings.'''
        # TODO: Properly escape the URI. For now we conveniently limit
        # ourselves to URIs that don't need encoding.
        return '<%s>' % (self.uri,)

    def get_articles(self):
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
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri_as_ntriples()}) 
        # return the dictionary resultset of the query          
        return resultSet
