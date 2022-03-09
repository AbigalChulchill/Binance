from django.db import models

# Create your models here.


class UserBot(models.Model):

    MODES = [
        ('H', 'HARD'),
        ('L', 'LITE'),
    ]

    chat_id = models.IntegerField(primary_key=True)
    mode = models.CharField(null=True, max_length=10, choices=MODES, default='L')
    username = models.CharField(null=True, max_length=50)
    api_key = models.CharField(null=True, max_length=150)
    api_secret = models.CharField(null=True, max_length=150)

    def __str__(self):
        return str(self.username) + "|" + str(self.chat_id)

    class Meta:
        verbose_name_plural = 'Users'


class SymbolPair(models.Model):
    symbol1 = models.CharField(max_length=15, null=False)
    symbol2 = models.CharField(max_length=15, null=False)
    interval = models.CharField(max_length=5, null=False)
    open_percent = models.FloatField(null=True)
    close_percent = models.FloatField(null=True)

    def __str__(self):
        return f'{self.symbol1}/{self.symbol2} {self.interval} {self.open_percent}/{self.close_percent}'

    def save(self, *args, **kwargs):
        if len(SymbolPair.objects.filter(symbol1=self.symbol1, symbol2=self.symbol2, interval=self.interval)) == 0:
            super().save(*args, **kwargs)

            users_bot = UserBot.objects.all()

            for user in users_bot:
                UserPair.objects.create(user_bot=user, symbol_pair=self).save()
        else:
            super().save(*args, **kwargs)

    class Meta:
        unique_together = ('symbol1', 'symbol2', 'interval')
        verbose_name_plural = 'Symbols'


class UserPair(models.Model):

    STATUSES = [
        ('N', 'NONE'),
        ('O', 'OPEN'),
        ('C', 'CLOSE'),
    ]

    user_bot = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    symbol_pair = models.ForeignKey(SymbolPair, on_delete=models.CASCADE, null=True)
    status = models.CharField(null=False, default='N', max_length=10, choices=STATUSES)

    def open(self):
        self.status = 'O'

    def __str__(self):
        return str(self.user_bot) + "|" + str(self.symbol_pair)

    class Meta:
        unique_together = ('user_bot', 'symbol_pair')
        verbose_name_plural = 'User pairs'


class WhiteList(models.Model):
    username = models.CharField(max_length=50, null=False, unique=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name_plural = 'White List'
