###################################################################################
# UpdatEngine - Software Packages Deployment and Administration tool              #  
#                                                                                 #
# Copyright (C) Yves Guimard - yves.guimard@gmail.com                             #
#                                                                                 #
# This program is free software; you can redistribute it and/or                   #
# modify it under the terms of the GNU General Public License                     #
# as published by the Free Software Foundation; either version 2                  #
# of the License, or (at your option) any later version.                          #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program; if not, write to the Free Software                     #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA. #
###################################################################################

from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

from inventory.views import post
from inventory.machine import machineviews
from django.contrib.admin import site
import adminactions.actions as actions

# register all adminactions
site.add_action(actions.mass_update)
site.add_action(actions.export_as_csv)

urlpatterns = [ 
    url(r'^machine/(?P<machine_id>\d+)/$', machineviews),
    url(r'^grappelli/', include('grappelli.urls')),
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^post/', post),
    url(r'^adminactions/', include('adminactions.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^', include(admin.site.urls)),
]
# Use lines below only during development if you want django 
# to server static files

#urlpatterns += staticfiles_urlpatterns()
#urlpatterns += patterns('',
#		       (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
#		       (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
#		)
#if settings.DEBUG:
#	urlpatterns += patterns('', url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT,}),)
