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
from georgia_lynchings.utils import solr_interface  

logger = logging.getLogger(__name__)

# solr fields we want for creating timemap json
TIMEMAP_VIEW_FIELDS = [ 'row_id', 'label', 'min_date', 'max_date',
                        'victim_county_brundage', 'victim_allegedcrime_brundage']

class Timemap:
    '''The main class for creating json data for timemap display.
    '''

    def __init__(self, filters=None):
        
        # Get a list of all the potential Macro Events to map
        self.me_list = []
        macs = MacroEvent.all_instances()
        for mac in macs: self.me_list.append(mac.id) 
        
        # Add filter capabilities
        self.filterTags = {}        
        if filters is None:
            self.filters = []
        else:
            self.filters = filters

    def get_json(self):
        '''Get json object for timemap display.
        '''
        #TODO: get data from triplestore instead of solr
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
            :param filters: list of filter tags            
        '''
        
        ''' Set up a dictionary of filters to contain a dictionary of 
        tags and their frequency
        '''
        
        # Initialize filters for their tags and frequency
        for fitem in self.filters:
            self.filterTags[fitem] = {}

        # Timemap JSON Result initialization
        jsonResult = [{"id":"event", "title":"Events","theme":"red","type":"basic","options":{'items':[]}}] 
            
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
                    jsonResult[0]['options']['items'].append(self.create_timemap_item(solr_item, county, all_tag_list))
                # Display missing data items
                elif county not in geo_coordinates.countymap: 
                    logger.info(" Did not add macro event %s because county [%s] not defined in geo_coordinates" % (solr_item['row_id'], county))                    
                else: 
                    logger.info(" Did not add macro event %s because min_date not defined." % (solr_item['row_id']))
            except:
                logger.info(" Timemap timemap_format error on macro event [%s]." % solr_item['row_id'])
        
        if settings.DEBUG:        
            # This will output the list of filters with their tags and frequency to the log 
            logger.debug("FILTERS:")       
            for fitem in self.filters:
                logger.debug("FILTER TAGS for %s:" % fitem)
                for w in sorted(self.filterTags[fitem], key=self.filterTags[fitem].get, reverse=True):
                    logger.debug("%-25s %d" % (w, self.filterTags[fitem][w]))            
                              
        return jsonResult
        
    def create_timemap_item(self, solr_item, county, all_tag_list):
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
        
        # Add tags to pinpoint popup
        #print "\n ALL TAG LIST = [%s]\n" % ", ".join(all_tag_list)
        tag_list = "[" + ", ".join(all_tag_list) + "]"         
        moreinfo.append("<div>Tags: %s</div>" % tag_list)      
        
        # FIXME: use reverse
        # reverse('events:details', kwargs={'id': solr_item['row_id']})
        moreinfo.append("<div><a target='_blank' href='../%s/details'>more info</a></div>" % solr_item['row_id'])
        moreinfo_link = ''.join(moreinfo)
        
        item["options"]={'infoHtml': moreinfo_link.encode('ascii'), 'tags': tag_list.encode('ascii')} 

        return item
