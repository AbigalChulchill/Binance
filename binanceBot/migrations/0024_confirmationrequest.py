# Generated by Django 4.0.3 on 2022-03-13 12:11

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0023_rename_default_deposit_userbot_deposit_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short', models.CharField(max_length=50)),
                ('long', models.CharField(max_length=50)),
                ('deposit', models.FloatField()),
                ('create_datetime', models.DateTimeField(default=datetime.datetime(2022, 3, 13, 15, 11, 8, 347120))),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='binanceBot.symbolpair')),
                ('user_bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='binanceBot.userbot')),
            ],
        ),
    ]
