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

from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, pre_delete
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from inventory.models import machine
import hashlib
import os
import string
import random
import shutil
import zipfile
from django.core import serializers
from django.conf import settings
from inventory.models import entity
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.urls import reverse


def random_directory(size=8, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits, prefix='', suffix=''):
    random_string = ''.join(random.choice(chars) for x in range(size))
    return prefix+random_string+suffix


class packagecondition(models.Model):
    choice_yes_no = (
        ('yes', _('package|yes')),
        ('no', _('package|no'))
    )
    choice = (
        ('installed',  _('installed')),
        ('notinstalled', _('notinstalled')),
        ('lower', _('lower')),
        ('higher', _('higher')),
        ('system_is', _('operating_system_is')),
        ('system_not', _('operating_system_not')),
        ('is_W64_bits', _('is_W64_bits')),
        ('is_W32_bits', _('is_W32_bits')),
        ('language_is', _('language_is')),
        ('hostname_in', _('hostname_in')),
        ('hostname_not', _('hostname_not')),
        ('username_in', _('username_in')),
        ('username_not', _('username_not')),
        ('ipaddr_in', _('ipaddr_in')),
        ('ipaddr_not', _('ipaddr_not')),
        ('vendor_in', _('vendor_in')),
        ('vendor_not', _('vendor_not')),
        ('product_in', _('product_in')),
        ('product_not', _('product_not')),
        ('type_in', _('type_in')),
        ('type_not', _('type_not')),
        ('isfile', _('isfile')),
        ('notisfile', _('notisfile')),
        ('isdir', _('isdir')),
        ('notisdir', _('notisdir')),
        ('isfiledir', _('isfiledir')),
        ('notisfiledir', _('notisfiledir')),
        ('hashis', _('hashis')),
        ('hashnot', _('hashnot')),
        ('exitcodeis', _('exitcodeis')),
        ('exitcodenot', _('exitcodenot'))
    )
    name = models.CharField(max_length=100, verbose_name=_('packagecondition|name'))
    depends = models.CharField(max_length=12, choices=choice, default='installed', verbose_name=_('packagecondition|depends'), help_text=_('packagecondition|depends help text'))
    softwarename = models.CharField(max_length=500, null=True, blank=True, default='undefined', verbose_name=_('packagecondition|softwarename'), help_text=_('packagecondition|softwarename help text'))
    softwareversion = models.CharField(max_length=500, null=True, blank=True, default='undefined', verbose_name=_('packagecondition|softwareversion'), help_text=_('packagecondition|softwareversion help text'))
    entity = models.ManyToManyField(entity, blank=True, verbose_name=_('packagecondition|entity'))
    editor = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name=_('packagecondition| condition last editor'))
    exclusive_editor = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('packagecondition|exclusive editor'))

    class Meta:
        verbose_name = _('packagecondition|package condition')
        verbose_name_plural = _('packagecondition|packages conditions')
        ordering = ['name']

    def get_condition_packages(self):
        retval = ''
        for c in package.objects.filter(conditions=self.id):
            retval += '<a href="%s">%s</a><br/>' % (reverse('admin:deploy_package_change', args=[c.id]), c.name)
        return mark_safe(retval[:-5])
    get_condition_packages.short_description = _('package|deployment packages')

    def __str__(self):
        return self.name


def content_file_name(self, name):
    return random_directory(prefix='package-file/', suffix='/'+name)


class package(models.Model):
    choice_yes_no = (
        ('yes', _('package|yes')),
        ('no', _('package|no'))
    )
    name = models.CharField(max_length=100, verbose_name=_('package|name'))
    description = models.CharField(max_length=500, verbose_name=_('package|description'))
    conditions = models.ManyToManyField('packagecondition', blank=True, verbose_name=_('package|conditions'))
    command = models.TextField(max_length=1000, verbose_name=_('package|command'), help_text=_('package|command help text'))
    packagesum = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('package|packagesum'))
    filename = models.FileField(upload_to=content_file_name, null=True, blank=True, verbose_name=_('package|filename'))
    ignoreperiod = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('package|ignore deploy period'))
    public = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('package| public package'))
    entity = models.ManyToManyField(entity, blank=True, verbose_name=_('package|entity'))
    editor = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name=_('package| package last editor'))
    exclusive_editor = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('package|exclusive editor'))

    class Meta:
        verbose_name = _('package|deployment package')
        verbose_name_plural = _('package|deployment packages')
        ordering = ['name']

    def get_conditions(self):
        retval = ''
        for c in self.conditions.all():
            retval += '<a href="%s">%s</a><br/>' % (reverse('admin:deploy_packagecondition_change', args=[c.id]), c.name)
        return mark_safe(retval[:-5])
    get_conditions.short_description = _('packageAdmin|get_conditions')

    def save(self, *args, **kwargs):
        # delete old file when replacing by updating the file
        try:
            p = package.objects.get(id=self.id)
            if p.filename != self.filename:
                if os.path.split(os.path.dirname(p.filename.path))[1] == 'package-file':
                    if p.filename != '':
                        p.filename.delete(save=False)
                else:
                    shutil.rmtree(os.path.dirname(p.filename.path))

        except:
            pass  # when new file then we do nothing, normal case
        super(package, self).save(*args, **kwargs)

    def md5_for_file(self, block_size=2**20):
        if self.filename == '':
            return 'nofile'
        f = open(self.filename.path, 'rb')
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    def __str__(self):
        return self.name


# Add a post_save function to update packagesum after each save on
# a package object
@receiver(post_save, sender=package)
def postcreate_package(sender, instance, created, **kwargs):
    # Update of packagesum field
    if not instance.filename:
        instance.packagesum = 'nofile'
    else:
        instance.packagesum = instance.md5_for_file()
    # Update of all package history wish are programmed
    for ph in packagehistory.objects.filter(package=instance, status='Programmed'):
        ph.name = instance.name
        ph.description = instance.description
        ph.command = instance.command
        ph.packagesum = instance.packagesum
        if instance.packagesum != 'nofile':
            ph.filename = instance.filename.path
        else:
            ph.filename = ''
        ph.save()

    post_save.disconnect(receiver=postcreate_package, sender=package)
    instance.save()
    post_save.connect(receiver=postcreate_package, sender=package)


@receiver(pre_delete, sender=package)
def predelete_package(sender, instance, **kwargs):
    if instance.filename.name != '':
        if os.path.split(os.path.dirname(instance.filename.path))[1] == 'package-file':
            instance.filename.delete(save=False)
        else:
            shutil.rmtree(os.path.dirname(instance.filename.path))


# call packages_changed only when packages m2m changed
@receiver(m2m_changed, sender=machine.packages.through)
def packages_changed(sender, action, instance, **kwargs):
    allpackages = instance.packages.all()
    # Create and update packagehistory object
    if action == 'post_add':
        for package in allpackages:
            obj, created = packagehistory.objects.get_or_create(machine=instance, package=package, status='Programmed')
            obj.name = package.name
            obj.description = package.description
            obj.command = package.command
            obj.packagesum = package.packagesum
            if package.packagesum != 'nofile':
                obj.filename = package.filename.path
            obj.save()
    # delete packagehistory object if just programmed and deleted from machine
    # Should use this: if action == 'post_remove':
    # But don't work: bug #16073 of Django
    # So try to remove from history at every m2m changed
    for package_history in packagehistory.objects.filter(machine=instance, status='Programmed'):
        if not machine.objects.filter(packages__in=allpackages).exists():
            package_history.delete()


class packagehistory(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('packagehistory|name'))
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name=_('packagehistory|description'))
    command = models.TextField(max_length=1000, null=True, blank=True, verbose_name=_('packagehistory|command'))
    packagesum = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('packagehistory|packagesum'))
    filename = models.CharField(max_length=500, null=True, blank=True, verbose_name=_('packagehistory|filename'))
    machine = models.ForeignKey(machine, on_delete=models.CASCADE, verbose_name=_('packagehistory|machine'))
    package = models.ForeignKey(package, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('packagehistory|package'))
    status = models.CharField(max_length=500, default='Programmed', null=True, blank=True, verbose_name=_('packagehistory|status'))
    date = models.DateTimeField(auto_now=True, verbose_name=_('packagehistory|date'))

    class Meta:
        verbose_name = _('packagehistory|package history')
        verbose_name_plural = _('packagehistory|packages history')
        ordering = ['date']

    def __str__(self):
        return self.name


class packageprofile(models.Model):
    choice_yes_no = (
        ('yes', _('package|yes')),
        ('no', _('package|no'))
    )
    name = models.CharField(max_length=100, verbose_name=_('packageprofile|name'))
    description = models.CharField(max_length=500, verbose_name=_('packageprofile|description'))
    packages = models.ManyToManyField('package', blank=True, verbose_name=_('packageprofile|packages'))
    parent = models.ForeignKey('self', null=True, blank=True, related_name='child', on_delete=models.SET_NULL, verbose_name=_('packageprofile|parent'))
    entity = models.ManyToManyField(entity, blank=True,  related_name='package_profile_entity', verbose_name=_('packageprofile|entity'))
    editor = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name=_('packageprofile| condition last editor'))
    exclusive_editor = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('packageprofile|exclusive editor'))

    class Meta:
        verbose_name = _('packageprofile|package profile')
        verbose_name_plural = _('packageprofile|packages profiles')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_all_parents(self, plist):
        if self.parent is not None and self.parent not in plist:
            plist.append(self.parent)
            return self.parent.get_all_parents(plist)
        else:
            return plist

    def get_soft(self, plist=list()):
        packlist = list()
        # Add packages of profile
        for package in self.packages.all():
            if package not in packlist:
                packlist.append(package)
        # Add packages of profile's parents
        # Need to pass list() as parameter, Django bug??
        for profile in self.get_all_parents(list()):
            for package in profile.packages.all():
                if package not in packlist:
                    packlist.append(package)
        return sorted(packlist, key=lambda package: package.name)

    def get_packages(self):
        retval = mark_safe('<br/>- '.join([p.name for p in self.get_soft()]))
        if len(retval): retval = mark_safe('- ' + retval)
        return retval
    get_packages.short_description = _('packageAdmin|get_packages')


class packagewakeonlan(models.Model):
    choice_yes_no = (
        ('yes', _('package|yes')),
        ('no', _('package|no'))
    )
    choice = (
        ('Programmed', _('packagewakeonlan|Programmed')),
        ('Completed', _('packagewakeonlan|Completed'))
    )
    name = models.CharField(max_length=100, unique=True, verbose_name=_('packagewakeonlan|name'), help_text=_('packagewakeonlan|packagewakeonlan help text'))
    description = models.CharField(max_length=500, verbose_name=_('packagewakeonlan|description'))
    machines = models.ManyToManyField('inventory.machine', blank=True, verbose_name=_('packagewakeonlan|machines to start'))
    date = models.DateTimeField(verbose_name=_('packagewakeonlan|start_time'))
    status = models.CharField(max_length=100, choices=choice, default='Programmed', verbose_name=_('packagewakeonlan|status'))
    entity = models.ManyToManyField(entity, blank=True,  related_name='packagewakonelan_entity', verbose_name=_('packagewakonelan|entity'))
    editor = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name=_('packagewakonelan| condition last editor'))
    exclusive_editor = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('packagewakonelan|exclusive editor'))

    class Meta:
        verbose_name = _('packagewakeonlan|package wakeonlan')
        verbose_name_plural = _('packagewakeonlan|packages wakeonlan')
        ordering = ['date']

    def __str__(self):
        return self.name


class timeprofile(models.Model):
    choice_yes_no = (
        ('yes', _('package|yes')),
        ('no', _('package|no'))
    )
    name = models.CharField(max_length=100, verbose_name=_('timeprofile|name'), help_text=_('timeprofile|timeprofile help text'))
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name=_('timeprofile|description'))
    start_time = models.TimeField(verbose_name=_('timeprofile|start_time'))
    end_time = models.TimeField(verbose_name=_('timeprofile|end_time'))
    entity = models.ManyToManyField(entity, blank=True, related_name='time_profile_entity', verbose_name=_('timeprofile|entity'))
    editor = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name=_('timeprofile| condition last editor'))
    exclusive_editor = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('timeprofile|exclusive editor'))

    class Meta:
        verbose_name = _('timeprofile|time profile')
        verbose_name_plural = _('timeprofile|time profiles')
        ordering = ['start_time']

    def __str__(self):
        return self.name


class impex(models.Model):
    choice_yes_no = (
        ('yes', _('package|yes')),
        ('no', _('package|no'))
    )
    name = models.CharField(max_length=100, unique=True, verbose_name=_('impex|name'))
    description = models.TextField(max_length=500, verbose_name=_('impex|description'))
    packagesum = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('impex|packagesum'))
    filename = models.FileField(upload_to=content_file_name, null=True, blank=True, default=None, verbose_name=_('impex|filename'))
    package = models.ForeignKey(package, null=True, blank=True, default=None, on_delete=models.SET_NULL, verbose_name=_('impex|package'))
    date = models.DateTimeField(auto_now=True, verbose_name=_('impex|date'))
    entity = models.ManyToManyField(entity, blank=True,  related_name='impex_entity', verbose_name=_('impex|entity'))
    editor = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name=_('impex| condition last editor'))
    exclusive_editor = models.CharField(max_length=3, choices=choice_yes_no, default='no', verbose_name=_('impex|exclusive editor'))

    # Function below allow us to display a link to download export packages in admin.py on a readonly filefield
    def filename_link(self):
        if self.filename:
            return mark_safe('<a href="%s">Export</a>' % (self.filename.url))
        else:
            return '---'
    filename_link.short_description = _('impex|filename_link')

    class Meta:
        verbose_name = _('impex|import/export')
        verbose_name_plural = _('impex|imports/exports')
        ordering = ['name']

    def save(self, *args, **kwargs):
        # delete old file when replacing by updating the file
        try:
            p = impex.objects.get(id=self.id)
            if p.filename != self.filename:
                p.filename.delete(save=False)
        except:
            pass  # when new file then we do nothing, normal case
        super(impex, self).save(*args, **kwargs)

    def md5_for_file(self, block_size=2**20):
        if self.filename == '':
            return 'nofile'
        f = open(self.filename.path, 'rb')
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    def __str__(self):
        return self.name


@receiver(post_save, sender=impex)
def postcreate_impex(sender, instance, created, **kwargs):
    from deploy.models import package, packagecondition
    # If we choose to make an export
    if instance.package is not None:
        pack = package.objects.get(pk=instance.package.id)
        packagelist = list()
        packagelist.append(pack)
        conditionlist = list()
        for cond in pack.conditions.all():
            conditionlist.append(cond)
        all_objects = packagelist + conditionlist
        data = serializers.serialize('json', all_objects)

        if not instance.filename or instance.filename == '':
            path = random_directory()
            fullpath = settings.MEDIA_ROOT+'/package-file/'+path
            os.mkdir(fullpath)
            instance.filename = 'package-file/'+path+'/export.zip'

        zip = zipfile.ZipFile(instance.filename.path, 'w', zipfile.ZIP_DEFLATED)
        if pack.filename is not None:
            try:
                zip.write(pack.filename.path, os.path.basename(pack.filename.name))
            except:
                pass
        zip.writestr('export.json', data)
        zip.close()
    # if we choose to make an import
    else:
        if instance.filename is not None or instance.filename != '':
            # Create package file directory
            path = random_directory()
            fullpath = settings.MEDIA_ROOT+'/package-file/'+path
            os.mkdir(fullpath)
            # Extract package's file
            zfile = zipfile.ZipFile(instance.filename)
            zfile.extractall(fullpath)
            zfile.close()
            # Create package object
            # Load Json file
            file = open(fullpath+'/export.json')
            condlist = list()
            idpack = None
            for obj in serializers.deserialize('json', file):
                # Package import:
                if type(obj.object) == package:
                    # get last id to create a unique one
                    try:
                        obj.object.id = int(package.objects.order_by('-pk')[0].id)+1
                    except IndexError:
                        obj.object.id = 1
                    obj.object.name = 'Import/ '+obj.object.name
                    if package.objects.filter(name=obj.object.name).exists():
                        obj.object.name = 'Import/ '+obj.object.name
                    # if object as filename, object is link to the uncompressed directory created with import
                    if obj.object.filename != '':
                        obj.object.filename = 'package-file/'+os.path.split(fullpath)[1]+'/'+os.path.basename(obj.object.filename.path)
                    else:
                        shutil.rmtree(fullpath)
                    obj.object.conditions.clear()
                    # import entity, editor and exclusive_editor from impex object
                    # can't save entity because m2m aren't saved at this time
                    obj.object.editor = instance.editor
                    obj.object.exclusive_editor = instance.exclusive_editor
                    obj.object.save()
                    instance.package = package.objects.get(id=obj.object.id)
                    idpack = obj.object.id
                # Condition import:
                if type(obj.object) == packagecondition:
                    if packagecondition.objects.filter(name=obj.object.name).exclude(
                            depends=obj.object.depends, softwarename=obj.object.softwarename,
                            softwareversion=obj.object.softwareversion).exists():
                        obj.object.name = 'Import/ '+obj.object.name
                    cond, created = packagecondition.objects.get_or_create(name=obj.object.name, depends=obj.object.depends, softwarename=obj.object.softwarename, softwareversion=obj.object.softwareversion)
                    # import editor and exclusive_editor from impex object
                    # can't save entity because m2m aren't saved at this time
                    cond.editor = instance.editor
                    cond.exclusive_editor = instance.exclusive_editor
                    cond.save()
                    condlist.append(cond)
            # Add new conditions to package imported from json file
            pack = package.objects.get(id=idpack)
            for cond in condlist:
                pack.conditions.add(cond)
            pack.save()

    instance.packagesum = instance.md5_for_file()
    post_save.disconnect(receiver=postcreate_impex, sender=impex)
    instance.save()
    post_save.connect(receiver=postcreate_impex, sender=impex)


@receiver(pre_delete, sender=impex)
def predelete_impex(sender, instance, **kwargs):
    if instance.filename.name != '':
        if os.path.split(os.path.dirname(instance.filename.path))[1] == 'package-file':
            instance.filename.delete(save=False)
        else:
            shutil.rmtree(os.path.dirname(instance.filename.path))
