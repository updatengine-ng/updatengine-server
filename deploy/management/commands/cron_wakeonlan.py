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

from django.core.management.base import BaseCommand
from deploy.models import packagewakeonlan
from datetime import datetime
from time import sleep
from django.utils.timezone import utc


class Command(BaseCommand):
    def handle(self, *args, **options):
        now = datetime.utcnow().replace(tzinfo=utc)
        for package in packagewakeonlan.objects.filter(status='Programmed', date__lt=now):
            for machine in package.machines.all():
                print('Wakeonlan of '+machine.name)
                machine.wakeup()
                sleep(3)
            package.status = 'Completed'
            package.save()
