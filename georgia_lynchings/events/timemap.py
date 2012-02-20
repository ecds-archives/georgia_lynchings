'''
Tool for creating JSON Object for usage in Timemap display.
'''
import logging

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
        
        ''' Create a dictionary of filters to contain a dictionary of 
        tags and their frequency
        '''

        # Timemap JSON Result initialization
        jsonResult = []
        
        # a metadata dictionary for a single macro event
        me_item = {}
            
        for item in metadata:
            
            # Collect all the information for a single macro event
            row_id = item['macro'].split('#r')[1]
            # macro event row id has changed; create json          
            if me_item and (not me_item['row_id'] == row_id): 
                for fdict in self.filters:
                    tag_list = []
                    # Create a list of unique filter items, default to "Not Available"
                    tag_list = me_item.get(fdict['qvar'], ['Not Available'])  
                    me_item[fdict['qvar']] = set(tag_list)               
                
                try:
                    # The macro event must geo coordinates for the timemap
                    if me_item['county'] in geo_coordinates.countymap:
                        jsonResult.append(self.create_item(me_item))
                    else: 
                        logger.info("Did not add macro event %s because county [%s] not defined in geo_coordinates" % (row_id, me_item['county']))
                except Exception, err:
                    logger.debug("Timemap format error on macro event [%s]; Error: %s" % (row_id, str(err)))
                    
                # finished adding macro event item, so reset macro event
                me_item = {}

            # parse metadata for this macro event.
            me_item['row_id'] = me_item.get('row_id', row_id)
            me_item['label'] = me_item.get('label', item.get('label')).encode('ascii')                  
            me_item['county'] = me_item.get('county', item.get('vcounty_brdg')).encode('ascii')            
            me_item['min_date'] = me_item.get('min_date', item.get('min_date')).encode('ascii')             
            me_item['max_date'] = me_item.get('max_date', item.get('max_date')).encode('ascii')
            if item.get('victim_allegedcrime_brundage', None):
                try:
                    alleged_crime = item['victim_allegedcrime_brundage'].encode('ascii')
                    me_item['victim_allegedcrime_brundage'].append(alleged_crime)
                except KeyError:
                    me_item['victim_allegedcrime_brundage']=[alleged_crime]                   

        return jsonResult
        
    def create_item(self, metadata):
        '''Create a pinpoint item for timemap json file
        
        :param metadata: a dictionary item from the metadata query result set   
        '''

        item={}         # create a timemap pinpoint item 
        
        # Add 'title', if defined
        item["title"]=metadata['label']
            
        # Add 'start' date
        item["start"]=metadata['min_date']
        
        # Add 'end' date if defined
        if metadata['max_date']:    item["end"]=metadata['max_date']
                
        # NOTE: geo_coordinates is a temporary solution until values are in PC-ACE.    
        # Add longitude and latitude values
        lat=geo_coordinates.countymap[metadata['county']]['latitude']
        lon=geo_coordinates.countymap[metadata['county']]['longitude']        
        item["point"]={"lat" : lat, "lon" : lon}
        
        # Add more info link to details page
        detail_link = reverse('details', kwargs={'row_id': metadata['row_id']})
            
        # infotemplate popup details
        item["options"]={'title': metadata['label'],
                        'min_date': metadata['min_date'],
                        'county':  metadata['county'],
                        'detail_link': detail_link}
                        
        # Create the tag list
        for fdict in self.filters:
            tag_list = "[" + ", ".join(metadata[fdict['qvar']]) + "]" 
            item["options"]['tags']= tag_list.encode('ascii')  
                          
        return item
