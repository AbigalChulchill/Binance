# Generated by Django 4.0.3 on 2022-03-09 19:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0008_alter_userpairs_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userpairs',
            unique_together={('user_bot', 'symbol_pair')},
        ),
    ]