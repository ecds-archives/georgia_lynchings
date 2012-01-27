from collections import defaultdict
from rdflib import Variable
from georgia_lynchings import query_bank
from georgia_lynchings.rdf.models import ComplexObject, \
    ReversedRdfPropertyField, ChainedRdfPropertyField
from georgia_lynchings.rdf.ns import scx, ssx, sxcxcx
from georgia_lynchings.rdf.sparql import SelectQuery
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
    victim = ssx.r82 # FIXME: data as of 2011-12-26 deprecates, favoring sxcxcx.r121
    'the name of the victim of the lynching'
    case_number = ssx.r84 # FIXME: not clear if data as of 2011-12-26 has this at all
    'a case number identifying this lynching case'

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

        data['triplet_label'] = [row['trlabel'] for row in self.get_triplets()]

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
        
        # set the macro event label, and load all the associated events
        ss=SparqlStore()
        query=query_bank.events['macro']         
        allResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        if allResultSet:
            results['melabel'] = allResultSet[0]['melabel'] 
            results['events'] = []
            for event in allResultSet:
                eventdict = {}
                if event['evlabel']:
                    eventdict['event']=event['event']
                    eventdict['evlabel']=event['evlabel']
                    results['events'].append(eventdict)
        
        # Do not continue if an event does not exist.
        if not results: return None
        
        # collect date information
        ss=SparqlStore()
        query=query_bank.events['all']         
        docResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        results['articleTotal'] = docResultSet[0]['articleTotal']                         
        
        # collect detail information
        ss=SparqlStore()
        query=query_bank.events['details']         
        detailResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                          
        reason_list = []
        outcome_list = []                             
        event_type_list = []
        if detailResultSet:
            for detail in detailResultSet: 
                # Get the name_of_reason, if defined.
                if 'reason' in detail.keys(): reason_list.append(detail['reason'])
                # Get the name_of_outcome, if defined.            
                if 'outcome' in detail.keys(): outcome_list.append(detail['outcome']) 
                # Create a list of type_of_events, if defined.            
                if 'event_type' in detail.keys():  event_type_list.append(detail['event_type'])

        # Set the lists to a string, eliminate duplicates
        if event_type_list:  results['event_type'] = '; '.join(set(event_type_list))
        else: results['event_type'] = "n/a" 
        if reason_list:  results['reason'] = '; '.join(set(reason_list))
        else: results['reason'] = "n/a"  
        if outcome_list:  results['outcome'] = '; '.join(set(outcome_list))
        else: results['outcome'] = "n/a"

        # collect date information
        ss=SparqlStore()
        query=query_bank.events['date_range']         
        dateResultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        if dateResultSet:
            for dateResult in dateResultSet:
                for event in results['events']:
                    if 'mindate' in dateResult.keys(): event['mindate'] = dateResult['mindate']
                    if 'maxdate' in dateResult.keys(): event['maxdate'] = dateResult['maxdate']

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
                        location = None                 
                        if 'city' in locResult.keys():
                            location = "%s (city)" % locResult[u'city']
                        if 'state' in locResult.keys():
                            if location: location += ", %s (state)" %  locResult['state']
                            else: location = locResult['state']                     
                        if 'county' in locResult.keys():                            
                            if location: location += ", %s (county)" %  locResult['county']
                            else: location = "%s County" %  locResult['county'] 
                        # Add/Append location to results
                        if location and 'location' in event.keys() : 
                            event['location'] += "; %s" %  location
                        elif location:  event['location'] = location
                    index =+ 1 
                lindex =+ 1
                
        # Collect semantic triplets for each event.        
        tripletResultSet = self.get_triplets_by_event()                           
        if tripletResultSet:       
            for event in results['events']:
                if tripletResultSet[event['evlabel']]:  
                    event['triplet_first'] = tripletResultSet[event['evlabel']][0]
                    event['triplet_rest'] = tripletResultSet[event['evlabel']][1:]
                    
        # collect participant information
        for p in ['uparto', 'uparts']:
            ss=SparqlStore()
            query=query_bank.events[p]
            partoResultSet = ss.query(sparql_query=query,
                                 initial_bindings={'macro': self.uri.n3()})
            if partoResultSet:
                for part in partoResultSet:
                    for event in results['events']:
                        if event['event'] == part['event']:
                            partdict = {}
                            # Set the first and last name, if defined
                            if 'fname' in part.keys() and 'lname' in part.keys(): 
                                partdict['name'] = "%s %s" % (part['fname'], part['lname'])
                            elif 'fname' in part.keys(): partdict['name'] = part['fname']
                            elif 'lname' in part.keys(): partdict['name'] = part['lname']
                            # Set the qualitative age, if defined
                            if 'qualitative_age' in part.keys(): partdict['age'] = part['qualitative_age']
                            if 'race' in part.keys(): partdict['race'] = part['race']
                            if 'gender' in part.keys(): partdict['gender'] = part['gender']
                            if 'name_of_indivd_actor' in part.keys(): partdict['role'] = part['name_of_indivd_actor']
                        if partdict:
                            if p in event.keys(): event[p].append(partdict)
                            else: event[p]= [partdict]

                                            
        # return the dictionary results of the details information          
        return results        
        
    def get_triplets(self):
        '''Get the semantic triplets related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It returns one row per triplet associated with this Macro
                Event, with the following bindings:
                  * `triplet`: the URI of the triplet
                  * `trlabel`: the label of the triplet
                  * `event`: the URI of the Event containing the triplet
                  * `evlabel`: the label of that Event
                  * `melabel`: the label of this Macro Event

                The matches are ordered by `event` and case-folded
                `trlabel`.
        '''
        query=query_bank.events['triplets']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        return resultSet

    def get_triplets_by_event(self):
        triplets = self.get_triplets()
        events = defaultdict(list)
        for triplet in triplets:
            events[triplet['evlabel']].append(triplet['trlabel'])
        return events
        
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


class Event(ComplexObject):
    '''An Event is an object type defined by the project's private PC-ACE
    database. It represents a particular news story within a lynching case
    and all of the individual semantic triplets associated with it.
    '''

    rdf_type = scx.r53
    'the URI of the RDF Class describing event objects'

    # complex fields potentially attached to an Event
    triplets = sxcxcx.r62
    'the semantic triplets associated with this event'
    space = sxcxcx.r77
    'a place associated with this event'

    # simplex fields potentially attached to an Event
    event_type = ssx.r52
    'a word or short phrase describing the type of event'

    # reverse and aggregate properties
    macro_event = ReversedRdfPropertyField(MacroEvent.events,
                                           result_type=MacroEvent)

# FIXME: patching MacroEvent.events from down here isn't great: it
# essentially means a little corner of the MacroEvent definition is way down
# here. need to find a better way to do this.
MacroEvent.events.result_type = Event


class SemanticTriplet(ComplexObject):
    '''A Semantic Triplet is an object type defined by the project's private
    PC-ACE database. It represents a single statement encoded from a news
    article.
    '''

    rdf_type = scx.r52
    'the URI of the RDF Class describing semantic triplet objects'

    # complex fields potentially attached to a Semantic Triplet
    participant_s = sxcxcx.r63
    'the subject of the statement'
    process = sxcxcx.r64
    'the verb of the statement'
    participant_o = sxcxcx.r65
    'the object of the statement'
    alternative = sxcxcx.r91
    'an alternate and potentially conflicting rendition of this triplet'

    # simplex fields potentially attached to a Semantic Triplet
    relation_to_next = ssx.r42
    'conjunction or subordinating phrase linking this triplet to the next'
    is_passive = ssx.r91
    'does the statement use passive voice? (typically specified only if true)'

    # reverse and aggregate properties
    event = ReversedRdfPropertyField(Event.triplets,
                                     result_type=Event)
    macro_event = ChainedRdfPropertyField(event, Event.macro_event)

    def index_data(self):
        data = super(SemanticTriplet, self).index_data().copy()

        macro_event = self.macro_event
        if macro_event:
            data['macro_event_uri'] = macro_event.uri

        return data

# FIXME: patching Event.triplets from down here isn't great: it essentially
# means a little corner of the Event definition is way down here. need to
# find a better way to do this.
Event.triplets.result_type = SemanticTriplet
