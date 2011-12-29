from django.conf.urls.defaults import *

'''
Patterns: 
'Events related to an Article'      articles 
'''
  
urlpatterns = patterns('georgia_lynchings.articles.views',
    url(r'', 'newspaper_articles', name="newspaper_articles"),                          # events by times    
)

