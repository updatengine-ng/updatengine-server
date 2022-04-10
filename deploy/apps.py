from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class UpdatEngineConfig(AppConfig):
    name = 'deploy'
    verbose_name = _("header|Deploy")
