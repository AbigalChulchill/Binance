import datetime
import django.utils.timezone
from django.db import models

# Create your models here.


class UserBot(models.Model):

    MODES = [
        ('H', 'HARD'),
        ('L', 'LITE'),
    ]

    chat_id = models.BigIntegerField(primary_key=True)
    mode = models.CharField(null=True, max_length=10, choices=MODES, default='L')
    username = models.CharField(null=True, max_length=50)
    api_key = models.CharField(null=True, max_length=150)
    api_secret = models.CharField(null=True, max_length=150)
    active = models.BooleanField(null=False, default=True)
    auto_mode = models.BooleanField(null=False, default=False)
    deposit = models.IntegerField(null=False, default=100)
    open_percent = models.FloatField(null=False, default=3)
    close_pnl = models.FloatField(null=False, default=1)

    def __str__(self):
        return str(self.username) + "|" + str(self.chat_id)

    class Meta:
        verbose_name_plural = 'Users'


class Pair(models.Model):
    symbol1 = models.CharField(max_length=15, null=False)
    symbol2 = models.CharField(max_length=15, null=False)
    interval = models.CharField(max_length=5, null=False)

    def __str__(self):
        return f'{self.symbol1}/{self.symbol2} {self.interval}'

    class Meta:
        unique_together = ('symbol1', 'symbol2', 'interval')
        verbose_name_plural = 'Symbols'


class OpenPair(models.Model):
    user_bot = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    pair = models.ForeignKey(Pair, on_delete=models.CASCADE)

    short = models.CharField(max_length=15, null=True)
    long = models.CharField(max_length=15, null=True)

    deposit = models.FloatField(null=False)

    class Meta:
        unique_together = ('user_bot', 'pair')
        verbose_name_plural = 'Open pairs'


class ConfirmationRequest(models.Model):
    user_bot = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    pair = models.ForeignKey(Pair, on_delete=models.DO_NOTHING)
    short = models.CharField(max_length=50, null=False)
    long = models.CharField(max_length=50, null=False)

    deposit = models.FloatField(null=False)

    create_datetime = models.DateTimeField(null=False, default=django.utils.timezone.now)

    text = models.CharField(max_length=500, null=False, default='')

    class Meta:
        unique_together = ('user_bot', 'pair')


class IgnorePair(models.Model):
    user_bot = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    pair = models.ForeignKey(Pair, on_delete=models.CASCADE)

    ignore_start = models.DateTimeField(null=False, default=django.utils.timezone.now)
    ignore_time = models.IntegerField(null=False)

    class Meta:
        unique_together = ('user_bot', 'pair')


class WhiteList(models.Model):
    username = models.CharField(max_length=50, null=False, unique=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name_plural = 'White List'
