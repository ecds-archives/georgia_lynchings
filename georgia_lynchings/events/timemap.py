'''
Tool for creating JSON Object for usage in Timemap display.
'''
import logging
from pprint import pprint
import sys

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

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
        
        :param metadata: macro event core metadata result set, plus
            any additional data for timemap filters.
        '''

        # Timemap JSON Result initialization
        jsonResult = [] 

        for key, value in metadata.items():
            # Create a macro event item
            macroevent_item = MacroEvent_Item(row_id=key, filters=self.filters)
            # Add the timemap filter json data to the macro event item
            macroevent_item.init_item(queryresults=value)
            # Add the macro event item to the final result.
            macroevent_item.process_json(jsonResult)

        return jsonResult
            
class GeoCoordinates(object):
    '''A class to serve the longitude and latitude geo coordinates for the county.
    '''  
    
    def __init__(self, county=None):
        '''Initialize the :class:`timemap.GeoCoordinates` with geo
        coordinates.

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
            :param filters:the timemap filter dictionary           
        '''
        self.jsonitem = {}
        
        # Initialize the row id of the macro event
        self.row_id = row_id
        
        # Setup the filters for this macro event item
        self.filters = filters
        self.jsonitem_filters = {}
        for filter in filters:
            self.jsonitem_filters[filter['name']] = []
        
    def init_item(self, queryresults=None):
        '''Initialize the jsonitem from the queryresults
        
        :param queryresults: the results from the triplestore query.
        '''
        try: 
            county = self.jsonitem.get('county', queryresults.get('vcounty_brdg')).encode('ascii')                
            geo = GeoCoordinates(county=county)
            self.jsonitem["point"]={"lat" : geo.lat, "lon" : geo.lon}            
            self.jsonitem["title"]=queryresults.get('label').encode('ascii')
            self.jsonitem["start"]=queryresults.get('min_date').encode('ascii') 
            self.jsonitem["end"]=queryresults.get('max_date').encode('ascii')
            # infotemplate popup details
            self.jsonitem["options"]={'title': queryresults.get('label'),
                            'min_date': queryresults.get('min_date'),
                            'county':  county,
                            'detail_link': reverse('events:details', kwargs={'row_id': self.row_id})}
            # add filter tags                        
            self.add_filter_tags(queryresults)
                        
        except KeyError, err:                  
            logger.debug("MacroEvent[%s] county[%s] not defined in geo_coordinates.py" % (self.row_id, err))

    def add_filter_tags(self, queryresults=None): 
        '''Add filter tags information to the json item
        
        :param queryresults: the results from the triplestore query.
        ''' 
        
        # List of all the slugified filter tags for macro event item        
        tag_list = []
        for filter in self.jsonitem_filters.keys():
            
            # The filter must be present for the infoTemplate to respond correctly.
            self.jsonitem["options"][filter +"_filter"]=['n/a']   
                     
            if filter in queryresults:
                # Create a list of slugified tags for this macro event item
                slug_list = []
                for filterdict in self.filters:
                    if filterdict['name'] == filter:
                        for tag in queryresults[filter]:
                            slug_list = slug_list + [slugify(filterdict['prefix'] + " " + tag)]
                
                # List of slugified tags searched by the filter
                tag_list = list(set(tag_list + slug_list))
                self.jsonitem["options"]['tags']= tag_list
                # List of display name tags shown in the pop up.
                display_list = list(set(self.jsonitem_filters[filter] + queryresults[filter]))
                self.jsonitem["options"][filter +"_filter"]= display_list

                
    def process_json(self, jsonResult):
        '''Process the jsonitem by appending the item to the final json result.
        
        :param jsonResult: the json of all the macro events for timemap display.
        '''
        # Append the macro event json item to the final JSON result.
        jsonResult.append(self.jsonitem)
