# ------------------------------------
# UpdatEngine - Clear package history
# ------------------------------------
# Keep the last 90 days of package history logs 
#
# do not forget to add to add a cron task:
# 00 6 * * * root /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py runscript clear_history
#
# Requirement: django-extensions
#

import datetime
from deploy.models import *
from django.utils.timezone import utc

def run():
    dt = datetime.datetime.utcnow().replace(tzinfo=utc)-datetime.timedelta(days=90)
    for p in packagehistory.objects.filter(date__lt=dt):
        p.delete()
