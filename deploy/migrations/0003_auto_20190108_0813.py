# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-01-08 12:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0002_auto_20180605_1910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packagecondition',
            name='depends',
            field=models.CharField(choices=[(b'installed', 'installed'), (b'notinstalled', 'notinstalled'), (b'lower', 'lower'), (b'higher', 'higher'), (b'system_is', 'operating_system_is'), (b'system_not', 'operating_system_not'), (b'is_W64_bits', 'is_W64_bits'), (b'is_W32_bits', 'is_W32_bits'), (b'language_is', 'language_is'), (b'hostname_in', 'hostname_in'), (b'hostname_not', 'hostname_not')], default=b'installed', max_length=12, verbose_name='packagecondition|depends'),
        ),
        migrations.AlterField(
            model_name='packagecondition',
            name='softwarename',
            field=models.CharField(blank=True, default=b'undefined', help_text='packagecondition|softwarename help text', max_length=500, null=True, verbose_name='packagecondition|softwarename'),
        ),
    ]
