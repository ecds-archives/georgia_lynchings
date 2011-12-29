from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.ns import scx, ssx, sxcxcx
from georgia_lynchings.rdf.sparqlstore import SparqlStore
from urllib import quote

class MacroEvent(ComplexObject):
    '''A Macro Event is an object type defined by the project's (currently
    private) PC-ACE database. It represents a lynching case and all of the
    individual events associated with it.
    '''

    # NOTE: Many of these relationships are defined in the private PC-ACE
    # database for this project. The URIs were found a priori by examining
    # the RDF data imported from the database setup tables.

    rdf_type = scx.r1
    'the URI of the RDF Class describing macro event objects'

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

            SELECT DISTINCT ?melabel ?event ?evlabel ?dd ?docpath ?paperdate ?papername ?articlepage
            WHERE {
              # First find all of the Macro events and all of the Events for those
              # Macros. Macros aren't strictly necessary, but they're provided
              # here for
              # context.
              ?macro a scx:r1;                   # Macro event
                     dcx:Identifier ?melabel;
                     sxcxcx:r61 ?event.          # Event
              ?event dcx:Identifier ?evlabel.

              # Report URI and file path of each document for the event
              ?dxcxd dxcxd:Complex ?event;
                     dxcxd:Document ?dd.
              optional { ?dd ssx:r68 ?paperdate }
              optional { ?dd ssx:r69 ?papername }
              optional { ?dd ssx:r73 ?articlepage }
              optional { ?dd ssx:r85 ?docpath }              
                            }
            ORDER BY ?event ?docpath
        '''
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        # create a link for the macro event articles
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


def get_events_by_locations():
    '''Get a list of events along with the location of the event.

    :rtype: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:

              * `macro`: the uri of the associated macro event
              * `melabel`: the macro event label
              * `event`: the uri of the event associated with this article
              * `evlabel`: the event label
              * `city`: a city associated with the event
              * `county`: a county associated with the event
              * `state`: a state associated with the event

            The matches are ordered by `city`, `county`, `state`, `evlabel`, and `event`.
    '''

    query = '''
        PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
        PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
        PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
        PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>

        SELECT DISTINCT ?state ?county ?city ?event ?evlabel ?melabel
        WHERE {
          # First find all the Macro events, all fo the Events for those macros,
          # and all fo the Triplets for those events. We'll be looking in these
          # triplets for locations.
          # Note: Technically we don't need the Macro events. They're provided here
          # only for context.
          ?macro a scx:r1;                    # Macro event
                 dcx:Identifier ?melabel;
                 sxcxcx:r61 ?event.           # Event
          ?event dcx:Identifier ?evlabel;
                 sxcxcx:r62 ?_1.              # Semantic Triplet

          # Every Triplet has a Process
          ?_1 sxcxcx:r64 ?_2.                 # Process

          # We need all of the places for that Process. There are four ways
          # they might be expressed:
          {
            ?_2 sxcxcx:r78 ?_3.               # Simple process
            ?_3 sxcxcx:r103 ?_4.              # Circumstances
            ?_4 sxcxcx:r106 ?_5.              # Space
          } UNION {
            ?_2 sxcxcx:r47 ?_6.               # Complex process
            ?_6 sxcxcx:r79 ?_3.               # Simple process
            ?_3 sxcxcx:r103 ?_4.              # Circumstances
            ?_4 sxcxcx:r106 ?_5.              # Space
          } UNION {
            ?_2 sxcxcx:r47 ?_6.               # Complex process
            ?_6 sxcxcx:r80 ?_7.               # Other process
            ?_7 sxcxcx:52 ?_3.                # Simple process
            ?_3 sxcxcx:r103 ?_4.              # Circumstances
            ?_4 sxcxcx:r106 ?_5.              # Space
          } UNION {
            ?_2 sxcxcx:r47 ?_6.               # Complex process
            ?_6 sxcxcx:r80 ?_7.               # Other process
            ?_7 sxcxcx:r53 ?_8.               # Nominalization
            ?_8 sxcxcx:r59 ?_5.               # Space
          }

          # Regardless of which way we came, ?_5 is some sort of place. If
          # we're going to get from there to location simplex data, there
          # are two different ways we can get there:
          {
            ?_5 sxcxcx:r2 ?_9.                # Territory
            ?_9 sxcxcx:r41 ?_10.              # Type of territory
          } UNION {
            ?_5 sxcxcx:r3 ?_10.               # City
          }

          # Grab the simplex data we're interested in, whichever are
          # available (but note that "?" is equivalent to missing data)
          OPTIONAL {
            ?_10 ssx:r18 ?county.             # County
            FILTER (?county != "?")
          }
          OPTIONAL {
            ?_10 ssx:r30 ?state.              # State
            FILTER (?state != "?")
          }
          OPTIONAL {
            ?_10 ssx:r55 ?city.               # City
            FILTER (?city != "?")
          }

          # And grab only those records that have at least one data point.
          FILTER (BOUND(?state) || BOUND(?county) || BOUND(?city))
        }
        # Order by UCASE to fold case.
        ORDER BY UCASE(?city) UCASE(?county) UCASE(?state) ?event ?evlabel
    '''
    ss=SparqlStore()
    resultSet = ss.query(sparql_query=query)
    # return the dictionary resultset of the query          
    return resultSet
    
def get_events_by_times():
    '''Get a list of events along with the times (date range) of the event.

    :rtype: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:

              * `macro`: the uri of the associated macro event
              * `melabel`: the macro event label
              * `event`: the uri of the event associated with this article
              * `evlabel`: the event label
              * `mindate`: the minimum date of the associated with the event
              * `maxdate`: the maximum date of the associated with the event

            The matches are ordered by `mindate`.
    '''

    query = '''
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
SELECT ?macro ?melabel ?event ?evlabel (MIN(?evdate) as ?mindate) (MAX(?evdate) as ?maxdate)
WHERE {
  ?macro a scx:r1;                  
         dcx:Identifier ?melabel;
         sxcxcx:r61 ?event.         
  ?event dcx:Identifier ?evlabel;
         sxcxcx:r62 ?_1.            
  ?_1 sxcxcx:r64 ?_2.               
  {
    ?_2 sxcxcx:r78 ?_3. 
    ?_3 sxcxcx:r103 ?_4. 
    ?_4 sxcxcx:r104 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.    
    ?_6 sxcxcx:r79 ?_7. 
    ?_7 sxcxcx:r103 ?_8. 
    ?_8 sxcxcx:r104 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.    
    ?_6 sxcxcx:r80 ?_9. 
    ?_9 sxcxcx:52 ?_7.    
    ?_7 sxcxcx:r103 ?_8. 
    ?_8 sxcxcx:r104 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.    
    ?_6 sxcxcx:r80 ?_9. 
    ?_9 sxcxcx:r53 ?_10. 
    ?_10 sxcxcx:r60 ?_5. 
  }

  ?_5 sxcxcx:r20 ?_11.  

  {
    ?_11 sxcxcx:r97 ?_12.     
    ?_12 ssx:r66 ?evdate      
  } UNION {
    ?_11 sxcxcx:r22 ?_13.     
    ?_13 sxcxcx:r4 ?_14.      
    ?_14 ssx:r66 ?evdate      
  } UNION {
    ?_11 sxcxcx:r22 ?_13.     
    ?_13 sxcxcx:r4 ?_14.      
    ?_14 ssx:r68 ?evdate 
  }
}
GROUP BY ?macro ?melabel ?event ?evlabel
ORDER BY ?mindate
'''
    ss=SparqlStore()
    resultSet = ss.query(sparql_query=query)
    # create a link for the macro event articles
    for result in resultSet:
        row_id = result['macro']['value'].split('#r')[1]
        result['macro_link'] = '../%s/articles' % row_id
    # return the dictionary resultset of the query          
    return resultSet    
