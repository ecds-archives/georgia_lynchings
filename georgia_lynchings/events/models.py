from georgia_lynchings import query_bank
from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.ns import scx, ssx, sxcxcx
from georgia_lynchings.rdf.sparqlstore import SparqlStore
from urllib import quote
import logging
from pprint import pprint

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

    def index_data(self):
        data = super(MacroEvent, self).index_data().copy()
        
        victim = self.victim
        if victim:
            data['victim'] = victim

        datedict = self.get_date_range()
        if datedict:
            data['min_date'] = datedict['mindate']
            data['max_date'] = datedict['maxdate']

        cities = self.get_cities()
        if cities:
            data['city'] = cities

        data['participant_uri'] = []
        data['participant_last_name'] = []
        data['participant_qualitative_age'] = []
        data['participant_race'] = []
        data['participant_gender'] = []
        data['participant_actor_name'] = []

        participant_rows = self.get_statement_object_data() + \
                           self.get_statement_subject_data()
        for participant_row in participant_rows:
            if 'parto' in participant_row:
                data['participant_uri'].append(participant_row['parto'])
            if 'parts' in participant_row:
                data['participant_uri'].append(participant_row['parts'])
            if 'lname' in participant_row:
                data['participant_last_name'].append(participant_row['lname'])
            if 'qualitative_age' in participant_row:
                data['participant_qualitative_age'].append(participant_row['qualitative_age'])
            if 'race' in participant_row:
                data['participant_race'].append(participant_row['race'])
            if 'gender' in participant_row:
                data['participant_gender'].append(participant_row['gender'])
            if 'name_of_indivd_actor' in participant_row:
                data['participant_actor_name'].append(participant_row['name_of_indivd_actor'])

        return data

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
            if 'docpath' not in result: result['docpath'] = 'n/a'
            else: 
                result['docpath_link'] = quote(result['docpath'].replace('\\', '/'))
                result['docpath'] = result['docpath'][10:] 
            if 'papername' not in result: result['papername'] = 'n/a'
            if 'paperdate' not in result: result['paperdate'] = 'n/a'
            if 'articlepage' not in result: result['articlepage'] = 'n/a'
        # return the dictionary resultset of the query          
        return resultSet
        
    def get_cities(self):
        '''Get all cities associated with this macro event.

        :rtype: a list of city names associated with this macro event,
                expressed as :class:`rdflib.Literal` objects (a subclass of
                ``unicode``)
        '''

        query=query_bank.events['cities']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return the list of cities
        return [result['city'] for result in resultSet]
        
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
                    datedict['mindate']=result['mindate']
                    datedict['maxdate']=result['maxdate']
                else: return None
            return datedict
        else: return None
        
    def get_details(self):
        '''Get all details associated with this macro event.

        :rtype: a mapping list of the type 
                It has the following bindings:
                  * `melabel`: the :class:`MacroEvent` label
                  * `article_link`: link to associated articles with this event
                  * `location`: location of the macro event 
                  * `date_range`: date_range of the macro event 
                  * `type`: type of the macro event  
                  * `reason`: reason for the macro event
                  * `outcome`: outcome for the macro event                   
                  * `victim`: the name of the victim
                  
           Example macro events: dcx2; dcx:r4, dcx:r50
        '''
        results = {}
        
        # collect date information
        ss=SparqlStore()
        query=query_bank.events['all']         
        allResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        results['articleTotal'] = allResultSet[0]['articleTotal']
     
        
        # collect date information
        ss=SparqlStore()
        query=query_bank.events['date_range']         
        dateResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        if dateResultSet:
            results['events'] = dateResultSet
     
        # collect location information
        ss=SparqlStore()
        query=query_bank.events['locations']         
        locationResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                           
        if locationResultSet:
            lindex = 0
            for locResult in locationResultSet:
                index = 0  
                for event in results['events']: 
                    if event['event'] == locResult['event']:
                        if u'city' in locResult:
                            if u'city' in results['events'][index]: 
                                results['events'][index][u'city'] = ', '.join(set([results['events'][index][u'city'],locResult[u'city']]))
                            else: event[u'city']= locResult[u'city']
                        if u'county' in locResult:
                            if u'county' in results['events'][index]: 
                                results['events'][index][u'county'] = ', '.join(set([results['events'][index][u'county'],locResult[u'county']]))
                            else: event[u'county']= locResult[u'county']
                        if u'state' in locResult:
                            if u'state' in results['events'][index]: 
                                results['events'][index][u'state'] = ', '.join(set([results['events'][index][u'state'],locResult[u'state']]))
                            else: event[u'state']= locResult[u'state']                               
                    index =+ 1 
                lindex =+ 1              
                
        # collect detail information
        ss=SparqlStore()
        query=query_bank.events['details']         
        detailResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        results['melabel'] = "n/a"                             
        results['reason'] = "n/a"
        results['outcome'] = "n/a"               
        event_type_list = []
        if detailResultSet:
            # Get the macro event label, if defined.
            if detailResultSet[0]['melabel']: results['melabel'] = detailResultSet[0]['melabel']            
            # Get the name_of_reason, if defined.
            if detailResultSet[0]['reason']: results['reason'] = detailResultSet[0]['reason']
            # Get the name_of_outcome, if defined.            
            if detailResultSet[0]['outcome']: results['outcome'] = detailResultSet[0]['outcome'] 
            # Create a list of type_of_events, if defined.
            for detail in detailResultSet: 
                if detail['type_of_event']:  event_type_list.append(detail['type_of_event'])
                
        # Set the event_type to a string, eliminate duplicates
        if event_type_list:  results['event_type'] = ', '.join(set(event_type_list))
        else: results['event_type'] = "n/a"

        # return the dictionary results of the details information          
        return results        
        
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
                if result['evlabel'] not in events:
                    events[result['evlabel']]=[]
                events[result['evlabel']].append(result['trlabel'])
            return events
        else: return None  
        
    def get_statement_object_data(self):
        '''Get data about the particpant-O (sentence object) of statements
        related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `lname`: lname of this actor 
                  * `qualitative_age`: qualitative_age of this actor                                   
                  * `race`: race of this actor 
                  * `gender`: gender of this actor 
                  * `name_of_indivd_actor`: Name of Individual Actor
                  * `actor`: actor of this participant-O 
                  * `parto`: participant-O of this triplet                                                                                         
                  * `triplets`: the semantic triplets related to this event               
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label
                  * `macro`: the macro event ID
        '''

        query=query_bank.events['parto']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary of the resultSet
        return resultSet
                                 
    def get_statement_subject_data(self):
        '''Get data about the particpant-S (sentence subject) of statements
        related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `lname`: lname of this actor 
                  * `qualitative_age`: qualitative_age of this actor                                   
                  * `race`: race of this actor 
                  * `gender`: gender of this actor 
                  * `name_of_indivd_actor`: Name of Individual Actor
                  * `actor`: actor of this participant-S 
                  * `parts`: participant-S of this triplet                                                                                         
                  * `triplets`: the semantic triplets related to this event               
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label
                  * `macro`: the macro event ID
        '''

        query=query_bank.events['parts']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary of the resultSet
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
        row_id = result['macro'].split('#r')[1]
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
        row_id = result['macro'].split('#r')[1]
        result['details_link'] = '%s/details' % row_id        
        result['articles_link'] = '%s/articles' % row_id
    # return the dictionary resultset of the query          
    return resultSet  
