'''
Tool for creating JSON Object for usage in Timemap display.
'''
import logging
from pprint import pprint
import sys

from django.core.urlresolvers import reverse

from georgia_lynchings import geo_coordinates
from georgia_lynchings.events.mapdata import Mapdata 

logger = logging.getLogger(__name__)

class Timemap(Mapdata):
    '''Extends :class:`georgia_lynchings.events.mapdata.Mapdata`. This is the
    main class for creating json data for timemap display.
    '''

    def __init__(self, filters= None, *args, **kwargs):
        
        # Add filter capabilities
        if filters is None:
            self.filters = []
        else:
            self.filters = filters
        
    def format(self, metadata):
        ''' Format the metadata results into a json structure for timemap.
        
            :param metadata: macro event metadata result set
        '''

        # Timemap JSON Result initialization
        jsonResult = [] 
        
        # A macro event item to be formatted into json for timemap
        macroevent_item = None       

        for queryresults in metadata:
            
            # Identify the item with a row_id
            row_id = queryresults['macro'].split('#r')[1]
            
            if macroevent_item and macroevent_item.row_id == row_id:
                # MacroEvent_Item already exists, so update filters                
                macroevent_item.add_filter_tags(queryresults)
            else:
                # Add current item to JsonResult
                if macroevent_item and macroevent_item.jsonitem and \
                    not macroevent_item.row_id == row_id:
                    macroevent_item.process_json(jsonResult)
                    
                # Create a new MacroEvent_Item
                macroevent_item = MacroEvent_Item(row_id, self.filters)
                macroevent_item.init_item(queryresults)

        # Process final item 
        macroevent_item.process_json(jsonResult)    

        return jsonResult
            
class GeoCoordinates(object):
    '''A class to serve the longitude and latitude geo coordinates for the county.
    '''  
    
    def __init__(self, row_id=None, county=None):
        '''Initialize the :class:`timemap.GeoCoordinates` with geo
        coordinates.
                
            :param row_id: macro event row id
            :param county: macro event county            
        '''
        self.lat=geo_coordinates.countymap[county]['latitude']
        self.lon=geo_coordinates.countymap[county]['longitude']
        
class MacroEvent_Item(object):
    '''A class to manage the macro event item
    '''  
    
    def __init__(self, row_id, filters):
        '''Initialize the :class:`timemap.MacroEvent_Item`
                
            :param row_id: macro event row id
            :param county: macro event county            
        '''
        self.jsonitem = {}
        
        # Initialize the row id of the macro event
        self.row_id = row_id
        
        # Setup the filters for this macro event item
        self.jsonitem_filters = {}
        for filter in filters:
            self.jsonitem_filters[filter['name']] = []
        
    def init_item(self, queryresults=None):
        '''Initialize the jsonitem from the queryresults
        
        :param queryresults: the results from the triplestore query.
        '''        
        try:            
            county = self.jsonitem.get('county', queryresults.get('vcounty_brdg')).encode('ascii')                
            geo = GeoCoordinates(row_id=self.row_id, county=county)      
            self.jsonitem["point"]={"lat" : geo.lat, "lon" : geo.lon}            
            self.jsonitem["title"]=queryresults.get('label').encode('ascii')
            self.jsonitem["start"]=queryresults.get('min_date').encode('ascii') 
            self.jsonitem["end"]=queryresults.get('max_date').encode('ascii')
            self.add_filter_tags(queryresults)

            # infotemplate popup details
            self.jsonitem["options"]={'title': queryresults.get('label'),
                            'min_date': queryresults.get('min_date'),
                            'county':  county,
                            'detail_link': reverse('events:details', kwargs={'row_id': self.row_id})}
        except KeyError, err:                  
            logger.debug("MacroEvent[%s] county[%s] not defined in geo_coordinates.py" % (self.row_id, err))
                
    def add_filter_tags(self, queryresults=None): 
        '''Add filter tags information to the json item
        
        :param queryresults: the results from the triplestore query.
        '''        
        for filter in self.jsonitem_filters.keys():
            if filter in queryresults:
                self.jsonitem_filters[filter].append(queryresults[filter].encode('ascii'))
        
    def process_json(self, jsonResult):
        '''Process the jsonitem with final filter tag list and append
        the item to the final json result
        
        :param jsonResult: the json of all the macro events for timemap display.
        '''         
        tag_list = []
        # FIXME: split out tags for multiple filters
        # Add the final filter tag list to the json item
        for filter in self.jsonitem_filters.keys():
            tag_list = "[" + ", ".join(set(self.jsonitem_filters[filter])) + "]"
            self.jsonitem["options"]['tags']= tag_list.encode('ascii')
            
        # Append the macro event json item to the final JSON result.
        jsonResult.append(self.jsonitem)    
