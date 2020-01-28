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

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save


class entity(models.Model):
    choice = (
        ('yes', _('yes')),
        ('no', _('no'))
    )
    name = models.CharField(max_length=100, unique=True, verbose_name=_('entity|name'))
    description = models.TextField(max_length=1000, verbose_name=_('entity|description'))
    parent = models.ForeignKey('self', null=True, blank=True, related_name='child', on_delete=models.SET_NULL, verbose_name=_('entity|parent'))
    packageprofile = models.ForeignKey('deploy.packageprofile', null=True, blank=True, related_name='pprofile', on_delete=models.SET_NULL, verbose_name=_('entity|package profile'), help_text=_('entity|packages profile help text'))
    old_packageprofile = models.ForeignKey('deploy.packageprofile', null=True, blank=True, on_delete=models.SET_NULL, related_name='old_packageprofile', verbose_name=_('entity|old package profile'), help_text=_('entity|old packages profile help text'))
    force_packageprofile = models.CharField(max_length=3, choices=choice, default='no', verbose_name=_('entity|force_packageprofile'))
    timeprofile = models.ForeignKey('deploy.timeprofile', null=True, blank=True, related_name='timeprofile', on_delete=models.SET_NULL, verbose_name=_('entity|time profile'), help_text=_('entity|time profile help text'))
    old_timeprofile = models.ForeignKey('deploy.timeprofile', null=True, blank=True, on_delete=models.SET_NULL, related_name='old_timeprofile', verbose_name=_('entity|old time profile'), help_text=_('entity|old time profile help text'))
    force_timeprofile = models.CharField(max_length=3, choices=choice, default='no', verbose_name=_('entity|force_timeprofile'))
    redistrib_url = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('entity|redistrib_url'))
    ip_range = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('entity|ip_range'), help_text=_('entity|ip range help text'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('entity|entity')
        verbose_name_plural = _('entity|entities')
        ordering = ['name']

    def get_children(self):
        '''Return a list composed of direct children'''
        return entity.objects.filter(parent=self)

    @staticmethod
    def get_all_children(query_entity, entity_list=list()):
        '''Return a list composed of all query_entity's children recursively'''
        for entity in query_entity:
            if entity not in entity_list:
                entity_list.append(entity)
                entity_children = entity.get_children()
                if entity_children:
                    entity_list + entity.get_all_children(entity_children, entity_list)
        return entity_list

    @staticmethod
    def get_all_parents(query_entity, entity_list=list()):
        '''Return a list composed of all query_entity's children recursively'''
        for entity in query_entity:
            if entity not in entity_list:
                entity_list.append(entity)
                entity_parent = entity.parent
                if entity_parent is not None:
                    entity_list + entity.get_all_parents([entity.parent], entity_list)
        return entity_list

    def id_all_children(self):
        '''Return a list composed of all children's id'''
        return list(e.id for e in self.get_all_children(self.get_children(), list()))

    @staticmethod
    def calculate_position(prefix=str(), current_entity=None, entity_list=list(), decal=False):
        level = 0
        if current_entity is None:
            all_root = entity.objects.filter(parent=None)
        else:
            all_root = entity.objects.filter(parent=current_entity)
        prefix_init = prefix
        for root in all_root:
            print(root.name)
            level += 1
            if prefix_init == '':
                prefix = '%s' % level
            else:
                prefix = '%s.%s' % (prefix_init, level)
            root.name = '%s - %s' % (prefix, root.name)
            entity_list.append(root.name)
            if len(root.get_children()) > 0:
                entity_list = entity.calculate_position(prefix, root, entity_list, True)
        return entity_list


class typemachine (models.Model):
    name = models.CharField(max_length=100, verbose_name=_('typemachine|name'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('typemachine|typemachine')
        verbose_name_plural = _('typemachine|typesofmachines')


class machine(models.Model):
    choice = (
        ('yes', _('yes')),
        ('no', _('no'))
    )
    serial = models.CharField(max_length=100, verbose_name=_('machine|serial'))
    name = models.CharField(max_length=100, verbose_name=_('machine|name'))
    vendor = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('machine|vendor'))
    product = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('machine|product'))
    domain = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('machine|domain'))
    uuid = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('machine|uuid'))
    username = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('machine|username'))
    language = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('machine|language'))
    entity = models.ForeignKey(entity, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('machine|entity'))
    packageprofile = models.ForeignKey('deploy.packageprofile', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('machine|package profile'), help_text=_('machine|packages profile help text'))
    timeprofile = models.ForeignKey('deploy.timeprofile', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('machine|time deploy profile'))
    lastsave = models.DateTimeField(auto_now=False, null=True, blank=True, verbose_name=_('machine|lastsave'))
    typemachine = models.ForeignKey(typemachine, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('machine|typemachine'))
    netsum = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('machine|netsum'))
    ossum = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('machine|ossum'))
    softsum = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('machine|softsum'))
    packages = models.ManyToManyField('deploy.package', blank=True, verbose_name=_('machine|packages'))
    manualy_created = models.CharField(max_length=3, choices=choice, default='yes', verbose_name=_('machine|manualy_created'))
    comment = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('machine|comment'))

    class Meta:
        verbose_name = _('machine|machine')
        verbose_name_plural = _('machine|machines')
        ordering = ['name']

    def get_pack_from_profile(self):
        return '\n'.join([p.name for p in self.packageprofile.packages.all()])

    def __str__(self):
        return self.name

    def wakeup(self):
        import struct
        import socket
        # Construct a six-byte hardware address
        for netcard in net.objects.filter(host=self):
            ethernet_address = str(netcard.mac)
            if ethernet_address != '00:00:00:00:00:00':
                addr_byte = ethernet_address.split(':')
                hw_addr = struct.pack(
                    'BBBBBB', int(addr_byte[0], 16),
                    int(addr_byte[1], 16),
                    int(addr_byte[2], 16),
                    int(addr_byte[3], 16),
                    int(addr_byte[4], 16),
                    int(addr_byte[5], 16))
                # Build the Wake-On-LAN 'Magic Packet'...
                msg = '\xff' * 6 + hw_addr * 16
                # ...and send it to the broadcast address using UDP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(msg, ('<broadcast>', 9))
                s.sendto(msg, ('<broadcast>', 7))
                s.close()

    def force_contact(self):
        import socket
        import time
        Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # definition des informations :
        Port = 2010
        try:
            for netcard in net.objects.filter(host=self):
                if netcard.ip != '127.0.0.1':
                    Sock.connect((netcard.ip, Port))
                    Sock.send(self.softsum.encode('utf-8'))
                    Sock.close()
                    time.sleep(1)
        except:
            pass


class osdistribution(models.Model):
    choice = (
        ('yes', _('yes')),
        ('no', _('no'))
    )
    name = models.CharField(max_length=100, verbose_name=_('osdistribution|name'))
    version = models.CharField(max_length=100, null=True, blank=True, default='undefined', verbose_name=_('osdistribution|version'))
    arch = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('osdistribution|arch'))
    systemdrive = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('osdistribution|systemdrive'))
    host = models.ForeignKey(machine, on_delete=models.CASCADE, verbose_name=_('osdistribution|host'))
    manualy_created = models.CharField(max_length=3, choices=choice, default='yes', verbose_name=_('osdistribution|manualy_created'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('osdistribution|osdistribution')
        verbose_name_plural = _('osdistribution|osdistributions')


class net(models.Model):
    choice = (
        ('yes', _('yes')),
        ('no', _('no'))
    )
    ip = models.CharField(max_length=50, verbose_name=_('net|ip'))
    mask = models.CharField(max_length=50, verbose_name=_('net|mask'))
    mac = models.CharField(max_length=100, verbose_name=_('net|mac'))
    host = models.ForeignKey(machine, on_delete=models.CASCADE, verbose_name=_('net|host'))
    manualy_created = models.CharField(max_length=3, choices=choice, default='yes', verbose_name=_('net|manualy_created'))

    def __str__(self):
        return self.ip

    class Meta:
        verbose_name = _('net|network')
        verbose_name_plural = _('net|networks')


class software(models.Model):
    choice = (
        ('yes', _('yes')),
        ('no', _('no'))
    )
    name = models.CharField(max_length=300, verbose_name=_('software|name'))
    version = models.CharField(max_length=500, null=True, blank=True, default='undefined', verbose_name=_('software|version'))
    uninstall = models.CharField(max_length=500, null=True, blank=True, default='undefined', verbose_name=_('software|uninstall'))
    host = models.ForeignKey(machine, on_delete=models.CASCADE, verbose_name=_('software|host'))
    manualy_created = models.CharField(max_length=3, choices=choice, default='yes', verbose_name=_('software|manualy_created'))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('software|software')
        verbose_name_plural = _('software|softwares')


# Add a post_save function to update packagesum after each save on
# a package object
@receiver(post_save, sender=entity)
def postsave_entity(sender, instance, created, **kwargs):
    # Update packageprofile for machine of entity
    if instance.force_packageprofile == 'yes':
        mm = machine.objects.filter(entity=instance)
    else:
        mm = machine.objects.filter(entity=instance, packageprofile=instance.old_packageprofile)

    for m in mm:
        m.packageprofile = instance.packageprofile
        m.save()

    if instance.force_timeprofile == 'yes':
        mm = machine.objects.filter(entity=instance)
    else:
        mm = machine.objects.filter(entity=instance, timeprofile=instance.old_timeprofile)

    for m in mm:
        m.timeprofile = instance.timeprofile
        m.save()

    post_save.disconnect(receiver=postsave_entity, sender=entity)
    instance.old_packageprofile = instance.packageprofile
    instance.old_timeprofile = instance.timeprofile
    instance.save()
    post_save.connect(receiver=postsave_entity, sender=entity)
