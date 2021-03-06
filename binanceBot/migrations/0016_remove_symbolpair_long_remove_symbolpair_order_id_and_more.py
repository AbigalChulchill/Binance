# Generated by Django 4.0.3 on 2022-03-10 23:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0015_symbolpair_long_symbolpair_order_id_symbolpair_short'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='symbolpair',
            name='long',
        ),
        migrations.RemoveField(
            model_name='symbolpair',
            name='order_id',
        ),
        migrations.RemoveField(
            model_name='symbolpair',
            name='short',
        ),
        migrations.AddField(
            model_name='userpair',
            name='long',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='userpair',
            name='order_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='userpair',
            name='short',
            field=models.CharField(max_length=15, null=True),
        ),
    ]
