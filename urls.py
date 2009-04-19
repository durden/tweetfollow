from django.conf.urls.defaults import *
from tweetfollow.tweetapp.views import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^tweetfollow/', include('tweetfollow.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
    (r'^$', home),
    (r'^login/$', login),
    (r'^logout/$', logout),
    (r'^users/$', users),
    (r'^refresh/$', refresh),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^tmedia/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_MEDIA_URL, 'show_indexes' : True}),)
