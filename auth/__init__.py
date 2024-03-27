from django.conf import settings

if not hasattr(settings, 'AUTH_LDAP_ALLOW_LOCAL_LOGON'):
    setattr(settings, 'AUTH_LDAP_ALLOW_LOCAL_LOGON', False)
