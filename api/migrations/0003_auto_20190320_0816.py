# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-20 08:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20190320_0805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='status',
            field=models.CharField(choices=[('NEW', 'new'), ('RENDERED', 'rendered'), ('PRINTER', 'printed')], max_length=8, verbose_name='Status of check'),
        ),
        migrations.AlterField(
            model_name='check',
            name='type',
            field=models.CharField(choices=[('KITCHEN', 'kitchen'), ('CLIENT', 'client')], max_length=7, verbose_name='Type of check'),
        ),
        migrations.AlterField(
            model_name='printer',
            name='check_type',
            field=models.CharField(choices=[('KITCHEN', 'kitchen'), ('CLIENT', 'client')], max_length=7),
        ),
    ]
