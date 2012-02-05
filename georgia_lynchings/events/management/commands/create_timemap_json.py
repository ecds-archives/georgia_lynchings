'''
**create_timemap_json** is a ``manage.py`` script to create ao timemap 
json file.

Example usage
^^^^^^^^^^^^^

Create timemap json with macro events::

  $ python manage.py create_timemap_json

'''

import os
import simplejson as json
import sys
from optparse import make_option
from pprint import pprint

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.utils import simplejson

from georgia_lynchings.events.models import MacroEvent, Victim
from georgia_lynchings import geo_coordinates

class Command(BaseCommand):
    '''Run a task to find all macro events in the triple store, 
    and create a json timemap file.'''
     
    help = __doc__

    def handle(self, *args, **options):
        
        # Initialize timemap task      
        if not hasattr(settings, 'TIMEMAP_JSON_URL') or not settings.TIMEMAP_JSON_URL:
            raise CommandError('TIMEMAP_JSON_URL must be configured in localsettings.py')
        timemap_url = settings.TIMEMAP_JSON_URL
        # NOTE: this is a temporary solution until geo coordinate values are in PC-ACE.
        self.geo = geo_coordinates.countymap
        # JSON Result initialization
        jsonResult = [{"id":"event", "title":"Events","theme":"red","type":"basic","options":{'items':[]}}]

        # Grab all the macro events and victims data
        macs = MacroEvent.all_instances()
        total = len(macs)
        self.stdout.write("Ready to process %d macro events\n" % (total))     
        victims = Victim.all_instances()        
        items = macs + victims  

        count = 0;  # progress counter
        
        for i, obj in enumerate(items):
            
            idx_data = obj.index_data()
            
            # skip over if county or min_date is not defined
            county = None               
            if 'victim_county_brundage' in idx_data and \
                len(idx_data['victim_county_brundage']) > 0:
                # use first county in list.
                county = str(idx_data['victim_county_brundage'][0])
            # Only add the timemap item, if the start date and county are defined
            # NOTE: at this time, victim_lynchingdate_brundage is not 
            # populated with data. If that changes, we should use this 
            # date as a backup for when min_date is not defined.            
            if 'min_date' in idx_data and county in self.geo:
                jsonResult[0]['options']['items'].append(self.getTimemapItem(idx_data, county))
            # Display missing data items
            elif county not in self.geo: 
                self.stdout.write(" Did not add macro event %s because county [%s] not defined in geo_coordinates\n" % (idx_data['row_id'], county))                    
            else: self.stdout.write(" Did not add macro event %s because min_date not defined.\n" % (idx_data['row_id']))
            
            # progress indicator
            if (count+1) % 10 == 0: 
                self.stdout.write(" Processed %d of %d Macro Events\n" % (count, total))
            else: self.stdout.write(".")
            count += 1
                        
        # output the json results to the timemap json url file
        json.dumps(jsonResult)
        filename = settings.MEDIA_ROOT + "/json/" + os.path.basename(settings.TIMEMAP_JSON_URL)         
        jsonfile = open(filename , "wb")
        jsonfile.write(json.dumps(jsonResult))
        jsonfile.close()
        self.stdout.write("\nDone\n")
        
    def getTimemapItem(self, idx_data, county):
        '''Create a pinpoint item for timemap json file'''
        
        item={}         # create a timemap pinpoint item 
        moreinfo = []   # text for pinpoint popup
        
        # Add 'title', if defined; add to pinpoint popup text
        if idx_data['label']:       
            item["title"]=str(idx_data['label'])
            moreinfo.append("<div><b>%s</b></div>" % (str(idx_data['label']))) 
            
        # Add 'start' date; add to pinpoint popup text
        item["start"]=str(idx_data['min_date'])
        moreinfo.append("<div>Start Date: %s</div>" % (str(idx_data['min_date'])))
        
        # Add 'end' date if defined
        if idx_data['max_date']:    item["end"]=str(idx_data['max_date'])
        
        # Add longitude and latitude values
        lat=self.geo[county]['latitude']
        lon=self.geo[county]['longitude']        
        item["point"]={"lat" : lat, "lon" : lon}
        
        # Add location to pinpoint popup 
        moreinfo.append("<div>Location: %s County</div>" % county)
        
        # FIXME: use reverse
        # reverse('events:details', kwargs={'id': idx_data['row_id']})
        moreinfo.append("<div><a target='_blank' href='../%s/details'>more info</a></div>" % str(idx_data['row_id']))
        moreinfo_link = ''.join(moreinfo)
        
        item["options"]={'infoHtml': str(moreinfo_link)}

        return item
