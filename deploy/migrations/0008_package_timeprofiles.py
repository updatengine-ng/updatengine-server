# Generated by Django 4.2.11 on 2024-05-08 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0007_package_use_global_variables_packagecustomvar'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='timeprofiles',
            field=models.ManyToManyField(blank=True, help_text='package|time profiles help text', to='deploy.timeprofile', verbose_name='package|time profiles'),
        ),
    ]