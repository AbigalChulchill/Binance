# Generated by Django 4.0.3 on 2022-03-05 21:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SymbolPairs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol1', models.CharField(max_length=15)),
                ('symbol2', models.CharField(max_length=15)),
                ('time_frame', models.CharField(max_length=5)),
            ],
            options={
                'unique_together': {('symbol1', 'symbol2')},
            },
        ),
        migrations.CreateModel(
            name='UserBot',
            fields=[
                ('chat_id', models.IntegerField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='UserPairs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='binanceBot.userbot')),
                ('symbols', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='binanceBot.symbolpairs')),
            ],
            options={
                'unique_together': {('chat_id', 'symbols')},
            },
        ),
    ]
