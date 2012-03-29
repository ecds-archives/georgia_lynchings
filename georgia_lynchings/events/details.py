'''
Details for a Macro Event.
'''
import logging
from pprint import pprint

from django.conf import settings
from django.core.urlresolvers import reverse

from georgia_lynchings import query_bank
from georgia_lynchings.rdf.sparqlstore import SparqlStore
from georgia_lynchings.events.models import MacroEvent, get_all_macro_events

logger = logging.getLogger(__name__)

class Details:
    '''The main class for creating details data for a Macro Event.
    '''
    
    def __init__(self, row_id):
        '''
        Identify the macro event 
                       :class:`~georgia_lynchings.events.models.MacroEvent`.
        for the details page.
        :param row_id: the numeric identifier for the 
                       :class:`~georgia_lynchings.events.models.MacroEvent`.
        '''        
        self.row_id = row_id
        self.me = MacroEvent(self.row_id)        

    def get(self):
        '''
        Get details for a
        :class:`~georgia_lynchings.events.models.MacroEvent`.
        '''
        results = {}
        
        # Get victim information.
        results = self.get_me_victims()
                
        # Get all the events associated with the macro event      
        eventsResultSet = self.me.get_events()
        
        # If no events or victims exist for this macro event, then return
        if not eventsResultSet and results is None:
            return None         

        # Load all the events for this macro event, 
        # include victim information when available
        if not results:
            results = self.get_me_events(eventsResultSet)
        else:
            results = dict(results.items() + self.get_me_events(eventsResultSet).items())

        # Collect semantic triplets for each event.
        self.update_me_triplets(results) 

        # Collect participant information
        self.update_me_participants(results, ['uparto', 'uparts'])

        # Set the title for the macro event
        results['melabel'] = self.get_me_title(eventsResultSet)

        # Set the Macro Event min/max date if available
        dateResultSet = self.me.get_date_range()
        if dateResultSet:
            results = dict(results.items() + self.me.get_date_range().items())
        
        # Set the detail information (Reason/Outcome/Event_Type)       
        detailResultSet = self.me.get_details()
        if detailResultSet:
            results = dict(results.items() + detailResultSet.items())
        
        # Set the articles for the macro event
        results['articleTotal'] = self.get_me_articles()            

        # Set the city location(s)    
        results['location'] = self.me.get_cities()
        
        return results
            
    def get_me_articles(self):
        ''' Get the count of related articles for this macro event.
        :rtype: a string of the article count        
        '''
        # TODO: Replace this with inline article information inline.
        
        try:
            ss=SparqlStore()
            query=query_bank.events['all']         
            docResultSet = ss.query(sparql_query=query, 
                                 initial_bindings={'macro': self.me.uri.n3()})
            return docResultSet[0]['articleTotal']    
        except Exception, err:
            logger.debug("article count is not found in this macro event %s; Error: %s" % (self.row_id, str(err)))
            return None        
   
    def get_me_events(self, evdict):   
        '''Return all the events for this macro event.
        
        :param evdict: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:               
            * `melabel`: the :class:`MacroEvent` label
            * `event`: the uri of the event associated with this article                  
            * `evlabel`: the event label
        :rtype: a dictionary of a list of events for this macro event 
            with the following bindings:
            * `event`: the uri of the event associated with this article                  
            * `evlabel`: the event label
        '''
        
        results = {}
        results['events'] = []
        for event in evdict:
            eventdict = {}
            if event['evlabel']:
                eventdict['event']=event['event']
                eventdict['evlabel']=event['evlabel']
                results['events'].append(eventdict)
        return results
            
    def get_me_title(self, evdict):   
        '''Return the macro event title.
        
        :param evdict: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:               
            * `melabel`: the :class:`MacroEvent` label
            * `event`: the uri of the event associated with this article                  
            * `evlabel`: the event label
        :rtype: a string of the title        
        '''
        try:
            return evdict[0].get('melabel', None)
        except Exception, err:
            logger.debug("melabel is not found in this macro event %s; Error: %s" % (self.row_id, str(err)))
            return None
            
    def get_name(self, first, last):   
        '''Return the name as firstname and lastname
        :param first: a string of the first name
        :param last: a string of the last name        
        :rtype: a string of the full name        
        '''
        if first and last:
            return first + " " + last
        elif first: return first
        elif last: return last
        else: return None
            
    def update_me_participants(self, detailDict, parts):
        '''Update the results with participants for this macro event.
        :param detailDict: a dictionary of the details
        :param parts: a list of participant types query keys.            
        '''      
        for p in parts:
            partResultSet = self.me.get_statement_data(p)
            
            if not partResultSet:
                return None
            for part in partResultSet:
                for event in detailDict['events']:
                    partdict = {}
                    # if the events match, then add participant info                
                    if event['event'] == part['event']:
                        partdict['name'] = self.get_name(part.get('fname', None),part.get('lname', None))
                        partdict['age'] = part.get('qualitative_age', None)
                        partdict['race'] = part.get('race', None)
                        partdict['gender'] = part.get('gender', None)
                        partdict['role'] = part.get('name_of_indivd_actor', None)
                        partdict['age'] = part.get('qualitative_age', None)
                        partdict['occupation'] = part.get('occupation', None)
                    if partdict:
                        if p in event.keys(): event[p].append(partdict)
                        else: event[p]= [partdict]                         
            
    def update_me_triplets(self, detailDict):   
        '''Update the triplets for this macro event in the details dictionary.
        :param detailDict: a dictionary of the details   
        '''
        tripletResultSet = self.me.get_triplets_by_event()
        if not tripletResultSet:
            return None                               
        for event in detailDict['events']:
            if tripletResultSet[event['evlabel']]:
                event['triplet_first'] = tripletResultSet[event['evlabel']][0]
                event['triplet_rest'] = tripletResultSet[event['evlabel']][1:]
                    
    def get_me_victims(self):
        '''Update the results with victim information for this macro event.
        :param detailDict: a dictionary of the details           
        '''
        victimResultSet = self.me.get_victim_data()
        if not victimResultSet:
            return None
            
        results = {}
        results['victims'] = []            
        for vic in victimResultSet:
            vicdict = {}
            vicdict['name'] = vic.get('vname_brdg', None)
            vicdict['county'] = vic.get('vcounty_brdg', None)
            vicdict['alleged_crime'] = vic.get('victim_allegedcrime_brundage', None)
            vicdict['lynching_date'] = vic.get('vlydate_brdg', None)
            vicdict['race'] = vic.get('vrace_brdg', None)
            if vicdict:
                try:
                    results['victims'].append(vicdict)
                except KeyError:
                    results['victims']= [vicdict]                          
                except Exception, err:
                    logger.debug("victim is not found in this macro event %s; Error: %s" % (self.row_id, str(err)))
                    return None
        return results
