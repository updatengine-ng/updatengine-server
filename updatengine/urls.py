###############################################################################
# UpdatEngine - Software Packages Deployment and Administration tool          #
#                                                                             #
# Copyright (C) Yves Guimard - yves.guimard@gmail.com                         #
#                                                                             #
# This program is free software; you can redistribute it and/or               #
# modify it under the terms of the GNU General Public License                 #
# as published by the Free Software Foundation; either version 2              #
# of the License, or (at your option) any later version.                      #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program; if not, write to the Free Software Foundation,     #
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.         #
###############################################################################

from django.urls import include, re_path
from django.contrib import admin
from inventory.views import post
from django.contrib.admin import site
import adminactions.actions as actions
from .views import check_version, ChangePasswordView

# Import admin module in each installed application
admin.autodiscover()

# Register all adminactions
site.add_action(actions.mass_update)
site.add_action(actions.export_as_csv)

urlpatterns = [
    re_path(r'^password_change/', ChangePasswordView.as_view()),
    re_path(r'^grappelli/', include('grappelli.urls')),
    re_path(r'^post/', post),
    re_path(r'^adminactions/', include('adminactions.urls')),
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    re_path(r'^check_version/$', check_version, name='latest_version'),
    re_path(r'', admin.site.urls),
]
