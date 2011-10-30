from django.conf.urls.defaults import patterns, include, url
from georgia_lynchings.views import current_datetime

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    #url(r'^home/$', 'georgia_lynchings.views.home', name="home"), 
    url(r'^time', 'georgia_lynchings.views.current_datetime', name="time"), 
    url(r'^$', 'georgia_lynchings.views.home', name="home"), 

    
      
    # Examples:
    #url(r'^$', 'georgia_lynchings.views.home', name='home'),
    # url(r'^georgia_lynchings/', include('georgia_lynchings.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),   
)
