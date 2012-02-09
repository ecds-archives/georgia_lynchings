'''
Tool for creating JSON Object for usage in Timemap display.
'''
from abc import abstractmethod, ABCMeta
import httplib2
import json
import logging

from django.conf import settings

from georgia_lynchings import geo_coordinates
from georgia_lynchings.events.models import MacroEvent
from georgia_lynchings.utils import solr_interface  

logger = logging.getLogger(__name__)

# solr fields we want for creating timemap json
TIMEMAP_VIEW_FIELDS = [ 'row_id', 'label', 'min_date', 'max_date',
                        'victim_county_brundage']

class Mapdata(object):
    '''The abstract class for creating json data for map display.
    :meth: `format` and :method: `create_item` methods should be overridden.
    '''

    __metaclass__ = ABCMeta


    def __init__(self, *args, **kwargs):
        
        # Get a list of all the potential Macro Events to map
        self.me_list = []
        macs = MacroEvent.all_instances()
        for mac in macs: self.me_list.append(mac.id) 

    def get_json(self):
        '''Get json object for map display.
        '''
        #TODO: get data from triplestore instead of solr
        return self.format(self.get_solr_data())
        
    def get_solr_data(self):
        '''Get the data from solr needed for map json content
        '''
        
        solr = solr_interface()
        mefilter = None         # macro event filter
        # find any objects with row_ids in the specified list
        # - generates a filter that looks like Q(row_id=1) | Q(row_id=22) | Q(row_id=135)
        for me in self.me_list:
            if mefilter is None:
                mefilter = solr.Q(row_id=unicode(me))
            else:
                mefilter |= solr.Q(row_id=unicode(me))  
        # TODO: restrict to macro events with min_date defined  
        solr_items = solr.query(mefilter) \
                        .field_limit(TIMEMAP_VIEW_FIELDS) \
                        .paginate(rows=20000) \
                        .sort_by('row_id') \
                        .execute()
        return solr_items
        
    @abstractmethod
    def format(self, solr_items):
        '''Format the solr results into a json structure for map display.
        **This method must be implemented in the subclass**
        
            :param solr_items: solr query result set      
        '''
        

    @abstractmethod
    def create_item(self, solr_item, county):
        '''Create a pinpoint item for map json file
        **This method must be implemented in the subclass**
        
        :param solr_item: a dictionary item from the solr query result set   
        :param county: string, victim_county_brundag   
                        
        '''
