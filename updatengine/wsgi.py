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

"""
WSGI config for updatengine project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys

path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if path not in sys.path:
    sys.path.append(path)

python_version = '.'.join(map(str, sys.version_info[:2]))
packages_path = 'lib/python%s/site-packages' % python_version
apps_path = os.path.join(os.path.join(os.path.dirname(path)), packages_path)
if apps_path not in sys.path:
    sys.path.append(apps_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'updatengine.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
