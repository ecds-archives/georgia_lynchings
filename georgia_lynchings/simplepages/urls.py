from django.conf.urls import patterns

urlpatterns = patterns('georgia_lynchings.simplepages.views',
	    url(r'^(?P<slug>)/$', 'view_page', name="view"),
    )
