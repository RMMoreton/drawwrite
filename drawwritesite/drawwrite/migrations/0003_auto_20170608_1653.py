# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-08 23:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drawwrite', '0002_auto_20170605_2005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Name'),
        ),
    ]