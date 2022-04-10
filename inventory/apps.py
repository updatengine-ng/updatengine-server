from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UpdatEngineConfig(AppConfig):
    name = 'inventory'
    verbose_name = _("header|Inventory")
