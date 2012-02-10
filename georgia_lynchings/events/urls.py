from django.conf.urls.defaults import *

'''
Patterns: 
'Articles related to an Event'      events/<row_id>/articles/ 
'Details related to an Event'       events/<row_id>/details/ 
'List all events, sorted by loc'    events/locations/ 
'List all events, sorted by time'   events/times/
'List all events, provide article count link'   events/
'''
  
urlpatterns = patterns('georgia_lynchings.events.views',

    url(r'locations/$', 'locations', name='locations'),                  # events by location
    url(r'times/$', 'times', name='times'),                              # events by times      
    url(r'search/$', 'search', name='search'),                           # event search results
    url(r'^(?P<row_id>[0-9]+)/articles/$', 'articles', name='articles'), # articles for macro event id
    url(r'^(?P<row_id>[0-9]+)/details/$', 'details', name='details'),    # articles for macro event id       
    url(r'^$', 'macro_events', name='macro_events'),                     # all macro event
    url(r'json/$','json_data', name='json-data'),                        # json data for map data
    url(r'timemap/$', 'timemap', name='timemap'),                        # timemap prototype
)

