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

from georgia_lynchings import geo_coordinates
from georgia_lynchings.events.timemap import Timemap
class Command(BaseCommand):
    '''Run a task to find all macro events in the triple store, 
    and create a json timemap file.'''
     
    help = __doc__

    def handle(self, *args, **options):
        
        # Get the json object require for creating a timemap json file
        timemap = Timemap()    
        jsonResult = timemap.get_json()
                        
        # output the json results to the timemap json url file
        json.dumps(jsonResult)
        filename = settings.MEDIA_ROOT + "/json/" + os.path.basename(settings.TIMEMAP_JSON_URL)         
        jsonfile = open(filename , "wb")
        jsonfile.write(json.dumps(jsonResult))
        jsonfile.close()
