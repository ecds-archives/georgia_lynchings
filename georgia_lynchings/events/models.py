from collections import defaultdict
from rdflib import Variable
from georgia_lynchings import query_bank
from georgia_lynchings.rdf.models import ComplexObject, \
    ReversedRdfPropertyField, ChainedRdfPropertyField, \
    RdfPropertyField
from georgia_lynchings.rdf.ns import scxn, ssxn, sxcxcxn
from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore
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

    rdf_type = scxn.Macro_Event
    'the URI of the RDF Class describing macro event objects'     
    
    # complex fields potentially attached to a MacroEvent
    
    events = sxcxcxn.Event
    'the events associated with this macro event'
    
    victims = RdfPropertyField(sxcxcxn.Victim, multiple=True)
    'the (new format) victims associated with this macro event'

    def index_data(self):
        data = super(MacroEvent, self).index_data().copy()
        
        # victims new format (mutliple victims and assoc. properties)
        data['victim_uri'] = []        
        data['victim_name_brundage'] = []
        data['victim_county_brundage'] = []
        data['victim_lynchingdate_brundage'] = []
        data['victim_race_brundage'] = []
        data['victim_allegedcrime_brundage'] = []
        # NOTE: victim age as qualitative_age and exact_age are available
        victim_rows = self.get_victim_data()
        if len(victim_rows) > 1: 
            logger.debug("Multiple [%d] Victims for event[%s]" % (len(victim_rows), victim_rows[0]['macro']))
        for victim_row in victim_rows:
            if 'victim' in victim_row:
                data['victim_uri'].append(victim_row['victim'])            
            if 'vname_brdg' in victim_row:
                data['victim_name_brundage'].append(victim_row['vname_brdg'])
            if 'vcounty_brdg' in victim_row:
                data['victim_county_brundage'].append(victim_row['vcounty_brdg'])
            if 'vlydate_brdg' in victim_row:
                data['victim_lynchingdate_brundage'].append(victim_row['vlydate_brdg'])
            if 'vrace_brdg' in victim_row:
                data['victim_race_brundage'].append(victim_row['vrace_brdg'])
            if 'vallegedcrime_brdg' in victim_row:
                data['victim_allegedcrime_brundage'].append(victim_row['vallegedcrime_brdg'])

        datedict = self.get_date_range()
        if datedict:
            data['min_date'] = datedict['mindate']
            data['max_date'] = datedict['maxdate']

        details = self.get_details()
        if details:
            data = dict(data.items() + details.items())            

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
                  * `event`: the uri of the event associated with this article                  
                  * `evlabel`: the event label
                  * `event_type`: the event type
                  * `outcome`: the name of the outcome                  
                  * `reason`: the name of the reason
        '''                
        query=query_bank.events['details']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})

        detailResult={}
        # return a unique list of event_types, reasons and outcomes
        for item in ['event_type', 'reason', 'outcome']:
            try:
                detailResult[item] = set([result[item] for result in resultSet])
            except:
                logger.debug("%s is not defined for macro event %s" % (item, self.uri.n3()))

        # return the list of cities
        return detailResult  
                
    def get_events(self):
        '''Get the events associated with this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:               
                  * `melabel`: the :class:`MacroEvent` label
                  * `event`: the uri of the event associated with this article                  
                  * `evlabel`: the event label
        '''                
        query=query_bank.events['macro']
        ss=SparqlStore()
        results = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})

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
        
    # TODO this will likely be replaced by get_statement_data
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

    # TODO this will likely be replaced by get_statement_data
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
        
    # Get unique participant (of type subject or object) data
    def get_statement_data(self, stmt_type):
        '''Get unique data about the particpant (sentence object or subject) 
        of statements related to this macro event.
        
        :param stmt_type: a type of participant 'uparto' or 'uparts' for
                unique participant subject or object.        

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `fname`: fname of this actor                 
                  * `lname`: lname of this actor 
                  * `qualitative_age`: qualitative_age of this actor                                   
                  * `race`: race of this actor 
                  * `gender`: gender of this actor 
                  * `name_of_indivd_actor`: Name of Individual Actor              
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label
                  * `macro`: the macro event ID
        '''

        query=query_bank.events[stmt_type]
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary of the resultSet
        return resultSet        
        
    def get_victim_data(self):
        '''Get the victim data related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It returns one row per victim associated with this Macro
                Event, with the following bindings:              
                  * `vname_brdg`: the (Brundage) name of the Victim
                  * `vcounty_brdg`: the (Brundage) county of the Victim
                  * `vallegedcrime_brdg`: the (Brundage) alleged crime of the Victim
                  * `vlydate_brdg`: the (Brundage) lynching date of the Victim
                  * `vrace_brdg`: the (Brundage) race of the Victim                                                                       
                  * `victim`: the URI of the Victim
                  * `vlabel`: the label of that Victim
                  * `melabel`: the label of this Macro Event
        '''
        query=query_bank.events['victims']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
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

    rdf_type = scxn.Event
    'the URI of the RDF Class describing event objects'

    # complex fields potentially attached to an Event
    triplets = sxcxcxn.Semantic_Triplet
    'the semantic triplets associated with this event'
    space = sxcxcxn.Space
    'a place associated with this event'

    # simplex fields potentially attached to an Event
    event_type = ssxn.Type_of_event
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

    rdf_type = scxn.Semantic_Triplet
    'the URI of the RDF Class describing semantic triplet objects'

    # complex fields potentially attached to a Semantic Triplet
    participant_s = sxcxcxn.Participant_S
    'the subject of the statement'
    process = sxcxcxn.Process
    'the verb of the statement'
    participant_o = sxcxcxn.Participant_O
    'the object of the statement'
    alternative = sxcxcxn.Alternative_triplet
    'an alternate and potentially conflicting rendition of this triplet'

    # simplex fields potentially attached to a Semantic Triplet
    relation_to_next = ssxn.Relation_to_next_triplet
    'conjunction or subordinating phrase linking this triplet to the next'
    is_passive = ssxn.Passive_no_agent
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

class Victim(ComplexObject):
    '''A Victim is an object type defined by the project's private
    PC-ACE database. It represents a Victim Grouping of a Macro Event and 
    several properties associated with it.
    '''

    rdf_type = scxn.Victim
    'the URI of the RDF Class describing victim objects'
    
    # simplex fields potentially attached to a Victim
    # Victim has a name (Brundage)
    victim_uri = sxcxcxn.Victim
    
    # simplex fields potentially attached to a Victim
    # Victim has a name (Brundage)
    victim_name = ssxn.Name_of_victim_Brundage

    # Victim has a county of lynching (Brundage)
    victim_county_of_lynching = ssxn.County_of_lynching_Brundage
        
    # Victim has an alleged crime (Brundage)        
    victim_alleged_crime = ssxn.Alleged_crime_Brundage
    
    # Victim has a date of lynchings (Brundage)    
    victim_date_of_lynching = ssxn.Date_of_lynching_Brundage
    
    # Victim has a race (Brundage)    
    victim_race = ssxn.Race_Brundage
                    
    # reverse and aggregate properties
    macro_event = ReversedRdfPropertyField(MacroEvent.victims,
                                           result_type=MacroEvent)

    def index_data(self):
        data = super(Victim, self).index_data().copy()

        macro_event = self.macro_event
        if macro_event:
            data['macro_event_uri'] = macro_event.uri

        return data

# FIXME: patching Victim from down here isn't great: it essentially
# means a little corner of the Victim definition is way down here. need to
# find a better way to do this.
MacroEvent.victims.result_type = Victim

