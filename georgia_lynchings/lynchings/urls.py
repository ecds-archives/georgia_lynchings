'''
URL patterns for events 
'''

from django.conf.urls.defaults import *

urlpatterns = patterns('georgia_lynchings.lynchings.views',
    url(r'^(?P<lynching_id>[0-9]+)/$', 'lynching_detail', name='lynching_detail'),
    url(r'^$', 'lynching_list', name='lynching_list'),                     # all macro event
    url(r'^accusations/$', 'alleged_crimes_list', name='alleged_crimes_list'),
    url(r'^accusations/(?P<accusation_id>[0-9]+)/$', 'lynching_list_by_accusation', name='lynching_list_by_accusation'),
    url(r'timemap/$', 'timemap', name='timemap'),                        # timemap prototype
    url(r'timemap/data/$','timemap_data', name='timemap_data'),
    url(r'counties/$','county_list', name='county_list'),
    url(r'^counties/(?P<county_id>[0-9]+)/$', 'county_detail', name='county_detail'),
)

