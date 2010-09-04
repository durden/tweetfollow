from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import *
from tweetapp.views import *

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
    (r'^$', register),
    (r'^register/$', register),
    (r'^about/$', direct_to_template, {'template': 'about.html'}),
    (r'^users/$', users),
    (r'^refresh/(.*)', update_followers),
    (r'^update/(.*)', update_followers),
    (r'^update_all/$', update_all),
    (r'^success/$', direct_to_template, {'template': 'success.html'}),
)
