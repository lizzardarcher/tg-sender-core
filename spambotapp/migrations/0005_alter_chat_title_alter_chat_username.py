# Generated by Django 4.2.5 on 2023-09-27 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spambotapp', '0004_tgadmin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='title',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='Название чата'),
        ),
        migrations.AlterField(
            model_name='chat',
            name='username',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='Ссылка или Юзернейм'),
        ),
    ]
