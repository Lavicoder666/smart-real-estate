# Generated by Django 3.2.6 on 2025-02-11 00:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0009_auto_20250211_0305'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='is_furnished',
        ),
        migrations.RemoveField(
            model_name='listing',
            name='photo_labels',
        ),
    ]
