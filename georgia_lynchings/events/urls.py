from django.conf.urls.defaults import *
from georgia_lynchings.events.event import Event

'''
Patterns: 
'Articles related to an Event'      events/<row_id>/articles/ 
'List all events, sorted by loc'    events/locations/ 
'List all events, sorted by time'   events/times/
'''
  
urlpatterns = patterns('events.views',
    url(r'^(?P<row_id>\d+)/articles/$', 'articles'),  # articles for macro event id
)

