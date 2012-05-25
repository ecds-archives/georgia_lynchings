from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('georgia_lynchings.reldata.views',
    url(r'^graph/$', direct_to_template, {'template': 'reldata/graph.html'}),
    url(r'^graph/data/$', 'graph_data', name='graph_data'),
)
