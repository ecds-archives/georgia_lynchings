'''
URL patterns for articles
'''

from django.conf.urls.defaults import *
  
urlpatterns = patterns('georgia_lynchings.articles.views',
    url(r'^$', 'newspaper_articles', name="newspaper_articles"),     # all articles
)

