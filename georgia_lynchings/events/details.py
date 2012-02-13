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

# solr fields we want for creating timemap json


class Details:
    '''The main class for creating details data for a Macro Event.
    '''

    def get(self, row_id):
        '''
        Get details for a
        :class:`~georgia_lynchings.events.models.MacroEvent`.
        
        :param row_id: the numeric identifier for the 
                       :class:`~georgia_lynchings.events.models.MacroEvent`.
        '''
        results = {}
        me = MacroEvent(row_id)
        
        # get the macro event label, and load all the associated events       
        eventsResultSet = me.get_events()
        if eventsResultSet:
            results['melabel'] = eventsResultSet[0]['melabel'] 
            results['events'] = []
            for event in eventsResultSet:
                eventdict = {}
                if event['evlabel']:
                    eventdict['event']=event['event']
                    eventdict['evlabel']=event['evlabel']
                    results['events'].append(eventdict)
                        
            # Macro Event Date Range
            dateResultSet = me.get_date_range()
            try:
                results['mindate'] = dateResultSet.get('mindate')
                results['maxdate'] = dateResultSet.get('maxdate')            
            except:
                logger.debug("Min/Max dates are not defined for macro event %s" % (row_id))
                    
            # Detail Information (Reason/Outcome/Event_Type)       
            detailResultSet = me.get_details()
            if detailResultSet:          
                for item in ['reason', 'outcome', 'event_type']:
                    results[item] = []          
                    # create a list of items            
                    for detail in detailResultSet: 
                        try:                     
                            results[item].append(detail[item])
                        except:
                            logger.debug("%s is not defined for macro event %s" % (item, row_id))                 
                    # create a string of unique items in list for display
                    try :
                        results[item] = "; ".join(set(results[item]))
                    except:
                        logger.debug("%s is not defined for macro event %s" % (item, row_id)) 
            
            # TODO: Replace this with inline article information inline.
            ss=SparqlStore()
            query=query_bank.events['all']         
            docResultSet = ss.query(sparql_query=query, 
                                 initial_bindings={'macro': me.uri.n3()})
            results['articleTotal'] = docResultSet[0]['articleTotal'] 
        

            # get cities associated with the macro event        
            try :
                results['location'] = "; ".join(set(me.get_cities()))
            except:
                logger.debug("There are no cities associated with this macro event %s" % (row_id))                    
                    
            # Collect semantic triplets for each event.        
            tripletResultSet = me.get_triplets_by_event()                           
            if tripletResultSet:       
                for event in results['events']:
                    if tripletResultSet[event['evlabel']]:  
                        event['triplet_first'] = tripletResultSet[event['evlabel']][0]
                        event['triplet_rest'] = tripletResultSet[event['evlabel']][1:]

           # collect participant information
            for p in ['uparto', 'uparts']:
                partoResultSet = me.get_statement_data(p)
                if partoResultSet:
                    for part in partoResultSet:
                        for event in results['events']:
                            partdict = {}                        
                            if event['event'] == part['event']:
                                partdict['name'] = " ".join([part.get('fname',''),part.get('lname','')]).strip()
                                partdict['age'] = part.get('qualitative_age','')
                                partdict['race'] = part.get('race','')
                                partdict['gender'] = part.get('gender','')
                                partdict['role'] = part.get('name_of_indivd_actor','')
                                partdict['age'] = part.get('qualitative_age','')
                            if partdict:
                                if p in event.keys(): event[p].append(partdict)
                                else: event[p]= [partdict]
            # TODO: change old format of simplex victim to new format complex victims (multiple)
            results['victim'] = me.victim
            return results
        else:
            return None
