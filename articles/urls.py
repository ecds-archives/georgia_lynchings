'''
URL patterns for articles
'''

from django.conf.urls.defaults import *

urlpatterns = patterns('georgia_lynchings.articles.views',
    url(r'^(?P<article_id>[0-9]+)/$', 'article_detail', name='detail'),
    url(r'^$', 'article_list', name='list'), 
)
