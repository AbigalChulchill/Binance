# Generated by Django 4.0.3 on 2022-03-07 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0005_remove_symbolpairs_need_percent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbot',
            name='username',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
