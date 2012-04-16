'''
URL patterns for events 
'''

from django.conf.urls.defaults import *
  
urlpatterns = patterns('georgia_lynchings.events.views',
    url(r'search/advanced/$', 'advanced_search', name='advanced_search'),# advanced event search
    url(r'search/$', 'search', name='search'),                           # event search results
    url(r'^(?P<row_id>[0-9]+)/articles/$', 'articles', name='articles'), # articles for macro event id
    url(r'^(?P<row_id>[0-9]+)/details/$', 'details', name='details'),    # details for macro event id       
    url(r'^$', 'macro_events', name='macro_events'),                     # all macro event
    url(r'map_json/$','map_json', name='map-json'),                      # json data for map data
    url(r'timemap/$', 'timemap', name='timemap'),                        # timemap prototype
)

