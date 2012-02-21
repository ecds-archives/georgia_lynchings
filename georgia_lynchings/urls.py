from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from georgia_lynchings.events.views import home

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^articles/', 'georgia_lynchings.articles.views.newspaper_articles', name="newspaper_articles"),
    url(r'^articles/', include('georgia_lynchings.articles.urls', namespace="articles")),    
    url(r'^events/', include('georgia_lynchings.events.urls', namespace="events")),
    url(r'^$', 'georgia_lynchings.events.views.home', name="home"), 
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),   
) 

# Production will serve media files through apache (see DEPLOYNOTES).
# Development setup for serving media files below:
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )
