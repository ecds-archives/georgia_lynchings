from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.ns import scx, ssx, sxcxcx
from georgia_lynchings.rdf.sparqlstore import SparqlStore
from georgia_lynchings import query_bank
from pprint import pprint
from urllib import quote
import logging

logger = logging.getLogger(__name__)

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

        query=query_bank.events['articles']
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
        
    def get_cities(self):
        '''Get all cities associated with this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `city`: the city
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label

                The matches are ordered by `event` and `docpath`.
        '''

        query=query_bank.events['cities']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return the list of cities
        if resultSet:
            citylist = []        
            for result in resultSet:              
                citylist.append(result['city']['value'])
            return citylist
        else: return None
        
    def get_date_range(self):
        '''Get minimum and maximum date range associated with this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `mindate`: the minimum date related to this event
                  * `maxdate`: the maximum date related to this event                  
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label

                The matches are ordered by `event` and `docpath`.
        '''

        query=query_bank.events['date_range']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary with min and max keys
        if resultSet:
            datedict = {}        
            for result in resultSet:
                if 'mindate' in result:
                    datedict['mindate']=result['mindate']['value']
                    datedict['maxdate']=result['maxdate']['value']
                else: return None
            return datedict
        else: return None
        
    def get_triplets(self):
        '''Get the semantic triplets related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `triplets`: the semantic triplets related to this event               
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label

                The matches are ordered by `event` and `docpath`.
        '''

        query=query_bank.events['triplets']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary of events that contains a list of triplets
        if resultSet:
            events = {}
            tripletlist = []        
            for result in resultSet:
                if result['evlabel']['value'] not in events:
                    events[result['evlabel']['value']]=[]
                events[result['evlabel']['value']].append(result['trlabel']['value'])
            return events
        else: return None                           

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
    logger.debug("events get_events_by_locations")
    query=query_bank.events['locations']    
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
    logger.debug("events get_events_by_times")
    query=query_bank.events['date_range']    
    ss=SparqlStore()
    resultSet = ss.query(sparql_query=query)
    # create a link for the macro event articles
    for result in resultSet:
        row_id = result['macro']['value'].split('#r')[1]
        result['macro_link'] = '../%s/articles' % row_id
    # return the dictionary resultset of the query          
    return resultSet    
    
def get_all_macro_events():
    '''Get a list of macro events along with number of linked articles.

    :rtype: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:

              * `macro`: the uri of the associated macro event
              * `melabel`: the macro event label
              * `articleTotal`: article count.

    '''
    logger.debug("events get_events_by_times")
    query=query_bank.events['all']    
    ss=SparqlStore()
    resultSet = ss.query(sparql_query=query)
    # create a link for the macro event articles
    for result in resultSet:
        row_id = result['macro']['value'].split('#r')[1]
        result['macro_link'] = '%s/articles' % row_id
    # return the dictionary resultset of the query          
    return resultSet       
