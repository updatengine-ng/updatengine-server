from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class UpdatEngineConfig(AppConfig):
    name = 'configuration'
    verbose_name = _("header|Configuration")
