# Generated by Django 4.0.3 on 2022-03-10 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0017_rename_order_id_userpair_order_id_long_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpair',
            name='order_id_long',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='userpair',
            name='order_id_short',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
