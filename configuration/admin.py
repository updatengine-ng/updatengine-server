###############################################################################
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

from configuration.models import deployconfig, subuser, globalconfig, userauth
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class deployconfigAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('name', 'activate_deploy', 'activate_time_deploy', 'start_time', 'end_time', 'entity',
                    'packageprofile', 'timeprofile')
    list_editable = ('activate_deploy', 'activate_time_deploy', 'start_time', 'end_time', 'entity', 'packageprofile',
                     'timeprofile')
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

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return True


class userauthInline(admin.TabularInline):
    model = userauth
    can_delete = False
    readonly_fields = ('ldap_auth',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return True


class UserAdmin(UserAdmin):
    # Display ldap_auth field only if LDAP backend is enabled
    if 'auth.backends.LDAPBackend' in settings.AUTHENTICATION_BACKENDS:
        list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'ldap_auth')

        def ldap_auth(self, instance):
            return instance.userauth.ldap_auth

        ldap_auth.short_description = _('LDAP')
        ldap_auth.boolean = True
        ldap_auth.admin_order_field = 'userauth__ldap_auth'

    # Override get_inlines method to display subuserInline inline only on edit page and userauthInline
    # based on enabled backends
    def get_inlines(self, request, obj):
        if not obj:
            return []
        if not 'auth.backends.LDAPBackend' in settings.AUTHENTICATION_BACKENDS:
            return [subuserInline]
        return [userauthInline, subuserInline]

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
            (_('Permissions'), {'fields': ('is_active', 'is_superuser',)}),
            (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            (_('Groups and permissions'), {'fields': ('groups', 'user_permissions')}),
        )
    else:
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
            # is_staff is automaticly set to True if is_active
            (_('Permissions'), {'fields': ('is_active', 'is_superuser',)}),
            (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            (_('Groups and permissions'), {'fields': ('groups',)}),
        )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(deployconfig, deployconfigAdmin)
admin.site.register(globalconfig, globalconfigAdmin)
