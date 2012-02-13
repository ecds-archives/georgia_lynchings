'''
Tool for creating JSON Object for usage in Timemap display.
'''
import httplib2
import json
import logging
from pprint import pprint

from django.conf import settings
from django.core.urlresolvers import reverse

from georgia_lynchings import geo_coordinates
from georgia_lynchings.events.models import MacroEvent
from georgia_lynchings.events.mapdata import Mapdata
from georgia_lynchings.utils import solr_interface  

logger = logging.getLogger(__name__)

# solr fields we want for creating timemap json


class Timemap(Mapdata):
    '''Extends :class:`georgia_lynchings.events.mapdata.Mapdata`. This is the
    main class for creating json data for timemap display.
    '''

    MAP_VIEW_FIELDS = [ 'row_id', 'label', 'min_date', 'max_date',
                        'victim_county_brundage', 'victim_allegedcrime_brundage']

    def __init__(self, filters= None, *args, **kwargs):
        super(Timemap, self).__init__(*args, **kwargs)
        
        # Add filter capabilities
        self.filterTags = {}        
        if filters is None:
            self.filters = []
        else:
            self.filters = filters

    def format(self, solr_items):
        ''' Format the solr results into a json structure for timemap.
        
            :param solr_items: solr query result set
        '''
        
        ''' Set up a dictionary of filters to contain a dictionary of 
        tags and their frequency
        '''
        
        # Initialize filters for their tags and frequency
        for fitem in self.filters:
            self.filterTags[fitem] = {}

        # Timemap JSON Result initialization
        jsonResult = [{"id":"event",
            "title":"Events",
            "theme":"red",
            "type":"basic",
            "infoTemplate": "<div><b>{{title}}</b></div><div>Start Date: {{start}}</div><div>Location: {{county}} County</div><div>Tags: {{tags}}</div><div><a target='_blank' href='{{detail_link}}'>more info</a></div>",
            "options":{
                'infoTemplate': "<div><b>{{title}}</b></div><div>Start Date: {{min_date}}</div><div>Location: {{county}} County</div><div>Tags: {{tags}}</div><div><a target='_blank' href='{{detail_link}}'>more info</a></div>",
                'items':[]
            }
        }] 
            
        for solr_item in solr_items:
            
            # For each filter item create a dict with key=tags value=freq
            all_tag_list = []
            for fitem in self.filters:
                # Create a frequency list of unique filter items, default to "Not Available"
                tag_list = solr_item.get(fitem, ['Not Available'])  
                for tag in set(tag_list):
                    self.filterTags[fitem][tag.encode('ascii')] = \
                        self.filterTags[fitem].get(tag.encode('ascii'), 0) + 1 
                    all_tag_list.append(tag.encode('ascii'))
                #TODO: for mulitple filters, find a way to distinguish tags w/in a filter

            # skip over if county or min_date is not defined  
            try:
                # use first county in list.
                county = solr_item.get('victim_county_brundage', [])[0]
                # Only add the timemap item, if the start date and county are defined
                # NOTE: at this time, victim_lynchingdate_brundage is not 
                # populated with data. If that changes, we should use this 
                # date as a backup for when min_date is not defined.            
                if 'min_date' in solr_item and county in geo_coordinates.countymap:
                    jsonResult[0]['options']['items'].append(self.create_item(solr_item, county, all_tag_list))
                # Display missing data items
                elif county not in geo_coordinates.countymap: 
                    logger.info(" Did not add macro event %s because county [%s] not defined in geo_coordinates" % (solr_item['row_id'], county))                    
                else: 
                    logger.info(" Did not add macro event %s because min_date not defined." % (solr_item['row_id']))
            except:
                logger.info(" Timemap format error on macro event [%s]." % solr_item['row_id'])
        
        if settings.DEBUG:        
            # This will output the list of filters with their tags and frequency to the log 
            logger.debug("FILTERS:")       
            for fitem in self.filters:
                logger.debug("FILTER TAGS for %s:" % fitem)
                for w in sorted(self.filterTags[fitem], key=self.filterTags[fitem].get, reverse=True):
                    logger.debug("%-25s %d" % (w, self.filterTags[fitem][w]))            
                              
        return jsonResult
        
    def create_item(self, solr_item, county, all_tag_list):
        '''Create a pinpoint item for timemap json file
        
        :param solr_item: a dictionary item from the solr query result set   
        :param county: string, victim_county_brundag
        :param all_tag_list: string, a combined list of tags for the filters
        '''
        
        item={}         # create a timemap pinpoint item 
        
        # Add 'title', if defined
        item["title"]=solr_item['label'].encode('ascii')
            
        # Add 'start' date
        item["start"]=solr_item['min_date'].encode('ascii')
        
        # Add 'end' date if defined
        if solr_item['max_date']:    item["end"]=solr_item['max_date'].encode('ascii')
        
        # NOTE: geo_coordinates is a temporary solution until values are in PC-ACE.    
        # Add longitude and latitude values
        lat=geo_coordinates.countymap[county]['latitude']
        lon=geo_coordinates.countymap[county]['longitude']        
        item["point"]={"lat" : lat, "lon" : lon}
        
        # Add tags to pinpoint popup
        tag_list = "[" + ", ".join(all_tag_list) + "]"          
        
        # Add more info link to details page
        detail_link = reverse('details', kwargs={'row_id': solr_item['row_id'].encode('ascii')})
        
        # infotemplate popup details
        item["options"]={'title': solr_item['label'].encode('ascii'),
                        'min_date': solr_item['min_date'].encode('ascii'),
                        'county': county.encode('ascii'),
                        'detail_link': detail_link,        
                        'tags': tag_list.encode('ascii')}
                                                
        return item
