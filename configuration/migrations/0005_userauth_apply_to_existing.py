# Manually added on 2024-04-29 07:32

from django.db import migrations
from django.contrib.auth.models import User
from configuration.models import userauth


def create_userauth(apps, schema_editor):
    users = User.objects.all()
    for user in users:
        if not hasattr(user, 'userauth'):
            userauth.objects.create(user=user)
            user.save()


class Migration(migrations.Migration):
    dependencies = [
        ('configuration', '0004_userauth'),
    ]

    operations = [
        migrations.RunPython(create_userauth)
    ]
