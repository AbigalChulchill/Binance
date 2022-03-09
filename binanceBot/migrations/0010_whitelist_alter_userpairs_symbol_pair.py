# Generated by Django 4.0.3 on 2022-03-09 20:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('binanceBot', '0009_alter_userpairs_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhiteList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='userpairs',
            name='symbol_pair',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='binanceBot.symbolpairs'),
        ),
    ]