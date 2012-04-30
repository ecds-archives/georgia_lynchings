'''
URL patterns for events 
'''

from django.conf.urls.defaults import *
  
urlpatterns = patterns('georgia_lynchings.events.views',
    url(r'search/advanced/$', 'advanced_search', name='advanced_search'),# advanced event search
    url(r'search/$', 'search', name='search'),                           # event search results
    url(r'^(?P<row_id>[0-9]+)/$', 'detail', name='detail'),
    url(r'^$', 'macro_events', name='macro_events'),                     # all macro event
    url(r'timemap/$', 'timemap', name='timemap'),                        # timemap prototype
    url(r'timemap/victim_data/$','timemap_victim_data',                  # victim data for timemap
        name='map-victim-data'),
)

