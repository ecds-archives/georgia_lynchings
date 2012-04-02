from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('georgia_lynchings.simplepages.views',
	    url(r'(?P<slug>[-\w]+)/$', 'view_page', name="view"),
    )
