from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('georgia_lynchings.reldata.views',
    url(r'^graph/$', 'graph', name='graph'),
    url(r'^graph/data/$', 'graph_data', name='graph_data'),
    url(r'^graph/events/$', 'event_lookup', name='event_lookup'),
    url(r'^wordcloud/$', 'wordcloud', name='wordcloud'),
    url(r'^wordcloud/data/$', 'cloud_data', name='cloud_data'),
)
