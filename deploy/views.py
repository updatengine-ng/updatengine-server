###############################################################################
# UpdatEngine - Software Packages Deployment and Administration tool          #
#                                                                             #
# Copyright (C) Yves Guimard - yves.guimard@gmail.com                         #
# Copyright (C) Noël Martinon - noel.martinon@gmail.com                       #
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

import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, Http404
from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse
from .models import package


@login_required
def download(request, filepath):
    if not request.user.is_superuser or not request.user.has_perm('deploy.change_package'):
        raise Http404()
    pkg = get_object_or_404(package, filename=filepath)
    filename = os.path.basename(filepath)
    chunk_size = 8192
    response = StreamingHttpResponse(
        FileWrapper(
            open(pkg.filename.path, "rb"),
            chunk_size,
        ),
        content_type='application/octet-stream',
    )
    response["Content-Length"] = os.path.getsize(pkg.filename.path)
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
