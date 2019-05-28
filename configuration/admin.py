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

from configuration.models import deployconfig, subuser, globalconfig
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class deployconfigAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('name', 'activate_deploy', 'activate_time_deploy', 'start_time', 'end_time', 'entity', 'packageprofile', 'timeprofile')
    list_editable = ('activate_deploy', 'activate_time_deploy', 'start_time', 'end_time', 'entity', 'packageprofile', 'timeprofile')
    list_display_links = ('name',)

    readonly_fields = ('name',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class globalconfigAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('name', 'show_warning', 'remove_duplicate')
    list_editable = ('show_warning', 'remove_duplicate')
    list_display_links = ('name',)
    readonly_fields = ('name',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class subuserInline(admin.TabularInline):
    model = subuser
    filter_horizontal = ('entity',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True


class UserAdmin(UserAdmin):
    # redefine get_form method to display subuserInline only on edit page
    def get_form(self, request, obj=None, **kwargs):
        '''
        Use special form during user creation
        '''
        defaults = {}
        if not obj:
            defaults.update({
                'form': self.add_form,
                'fields': admin.options.flatten_fieldsets(self.add_fieldsets),
            })
        else:
            self.inlines = (subuserInline,)
        defaults.update(kwargs)
        return super(UserAdmin, self).get_form(request, obj, **defaults)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            obj.is_staff = True
        else:
            obj.is_staff = False
        obj.save()

    if settings.SHOW_PERM_CONFIG_AUTH:
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
            # is_staff is automaticly set to True if is_active
            (_('Permissions'), {'fields': ('is_active', 'is_superuser', )}),
            (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            (_('Groups and permissions'), {'fields': ('groups', 'user_permissions')}),
        )
    else:
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
            # is_staff is automaticly set to True if is_active
            (_('Permissions'), {'fields': ('is_active', 'is_superuser', )}),
            (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            (_('Groups and permissions'), {'fields': ('groups',)}),
        )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(deployconfig, deployconfigAdmin)
admin.site.register(globalconfig, globalconfigAdmin)
