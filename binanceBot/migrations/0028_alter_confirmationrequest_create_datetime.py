# Generated by Django 4.0.3 on 2022-03-13 12:46

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0027_alter_confirmationrequest_create_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmationrequest',
            name='create_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
