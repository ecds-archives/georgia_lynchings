from django.conf.urls.defaults import *

'''
Patterns: 
'Events related to an Actor'      actors/<row_id>/macroevents/ 
'''
  
urlpatterns = patterns('georgia_lynchings.actors.views',
    url(r'^(?P<row_id>\d+)/macroevents/$', 'macroevents', name='macroevents'),  # events for actor id
)

