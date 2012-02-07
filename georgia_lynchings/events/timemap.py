'''
Tool for creating JSON Object for usage in Timemap display.
'''
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

class Timemap:
    '''The main class for creating json data for timemap display.
    '''

    def __init__(self):
        
        # Get a list of all the potential Macro Events to map
        self.me_list = []
        macs = MacroEvent.all_instances()
        for mac in macs: self.me_list.append(mac.id) 

    def get_json(self):
        '''Get json object for timemap display.
        '''
        return self.timemap_format(self.get_timemap_solr_data())
        
    def get_timemap_solr_data(self):
        '''Get the data from solr needed for timemap json content
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
        
    def timemap_format(self, solr_items):
        ''' Format the solr results into a json structure for timemap.
        
            :param solr_items: solr query result set      
        '''
        
        # Timemap JSON Result initialization
        jsonResult = [{"id":"event", "title":"Events","theme":"red","type":"basic","options":{'items':[]}}]     
        for solr_item in solr_items:
            
            # skip over if county or min_date is not defined  
            try:
                # use first county in list.
                county = solr_item.get('victim_county_brundage', [])[0]
                # Only add the timemap item, if the start date and county are defined
                # NOTE: at this time, victim_lynchingdate_brundage is not 
                # populated with data. If that changes, we should use this 
                # date as a backup for when min_date is not defined.            
                if 'min_date' in solr_item and county in geo_coordinates.countymap:
                    jsonResult[0]['options']['items'].append(self.create_timemap_item(solr_item, county))
                # Display missing data items
                elif county not in geo_coordinates.countymap: 
                    logger.info(" Did not add macro event %s because county [%s] not defined in geo_coordinates" % (solr_item['row_id'], county))                    
                else: 
                    logger.info(" Did not add macro event %s because min_date not defined." % (solr_item['row_id']))
            except:
                logger.info(" Timemap timemap_format error on macro event [%s]." % solr_item['row_id'])
        return jsonResult
        
    def create_timemap_item(self, solr_item, county):
        '''Create a pinpoint item for timemap json file
        
        :param solr_item: a dictionary item from the solr query result set   
        :param county: string, victim_county_brundag   
                        
        '''
        
        item={}         # create a timemap pinpoint item 
        moreinfo = []   # text for pinpoint popup
        
        # Add 'title', if defined; also add to pinpoint popup text
        item["title"]=solr_item['label'].encode('ascii')
        moreinfo.append("<div><b>%s</b></div>" % (solr_item['label'])) 
            
        # Add 'start' date; also add to pinpoint popup text
        item["start"]=solr_item['min_date'].encode('ascii')
        moreinfo.append("<div>Start Date: %s</div>" % (solr_item['min_date']))
        
        # Add 'end' date if defined
        if solr_item['max_date']:    item["end"]=solr_item['max_date'].encode('ascii')
        
        # NOTE: geo_coordinates is a temporary solution until values are in PC-ACE.    
        # Add longitude and latitude values
        lat=geo_coordinates.countymap[county]['latitude']
        lon=geo_coordinates.countymap[county]['longitude']        
        item["point"]={"lat" : lat, "lon" : lon}
        
        # Add location to pinpoint popup 
        moreinfo.append("<div>Location: %s County</div>" % county)
        
        # FIXME: use reverse
        # reverse('events:details', kwargs={'id': solr_item['row_id']})
        moreinfo.append("<div><a target='_blank' href='../%s/details'>more info</a></div>" % solr_item['row_id'])
        moreinfo_link = ''.join(moreinfo)
        
        item["options"]={'infoHtml': moreinfo_link.encode('ascii')}

        return item
