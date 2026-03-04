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

# auth/backends.py
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group, User
from django.contrib.auth.hashers import check_password
import ldap


class AuthBackend(ModelBackend):
    """ A custom authentication backend overriding django ModelBackend """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if not settings.AUTH_LDAP_ALLOW_LOCAL_LOGON:
                user =  User.objects.get(username=username, userauth__ldap_auth=False)
            else:
                user = User.objects.get(username=username)
            if not check_password(password, user.password):
                return None
        except User.DoesNotExist:
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class LDAPBackend(LDAPBackend):
    """ A custom authentication backend overriding django LDAPBackend """

    default_settings = {
        "GROUP_MAP": {},
    }

    def authenticate_ldap_user(self, ldap_user, password):
        user = ldap_user.authenticate(password)
        if user:
            user.set_password(password)
            user.userauth.ldap_auth = True
            user.save()
            ldap_groups_dns = ldap_user.group_dns
            for group_name, group_dn in self.settings.GROUP_MAP.items():
                group_dn = ldap.dn.dn2str(ldap.dn.str2dn(group_dn)).lower()
                if group_dn in ldap_groups_dns:
                    try:
                        group = Group.objects.get(name=group_name)
                        user.groups.add(group)
                    except Group.DoesNotExist:
                        print(
                            'Unable to add user to group \'%s\', the group does not exist. Available groups are %s' % (
                            group_name, {g.name for g in Group.objects.all()}))
                        pass
        return user
