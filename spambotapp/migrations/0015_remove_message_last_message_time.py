# Generated by Django 4.2.5 on 2023-09-30 08:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('spambotapp', '0014_remove_message_last_message_id_message_is_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='last_message_time',
        ),
    ]
