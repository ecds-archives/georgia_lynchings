'''
URL patterns for events 
'''

from django.conf.urls.defaults import *

urlpatterns = patterns('georgia_lynchings.lynchings.views',
    url(r'^(?P<story_id>[0-9]+)/$', 'story_detail', name='story_detail'),
    url(r'^$', 'story_list', name='story_list'),                     # all macro event
    url(r'^accusations/$', 'alleged_crimes_list', name='alleged_crimes_list'),
    url(r'^accusations/(?P<accusation_id>[0-9]+)/$', 'story_list_by_accusation', name='story_list_by_accusation'),
    url(r'timemap/$', 'timemap', name='timemap'),                        # timemap prototype
    url(r'timemap/data/$','timemap_data',                  # victim data for timemap
        name='timemap_data'),
)

