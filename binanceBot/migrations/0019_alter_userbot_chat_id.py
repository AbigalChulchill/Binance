# Generated by Django 4.0.3 on 2022-03-11 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0018_alter_userpair_order_id_long_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userbot',
            name='chat_id',
            field=models.BigIntegerField(primary_key=True, serialize=False),
        ),
    ]