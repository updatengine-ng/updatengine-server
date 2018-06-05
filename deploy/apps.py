from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class UpdatEngineConfig(AppConfig):
    name = 'deploy'
    verbose_name = _("header|Deploy")
