from django.db import models

# Create your models here.


class UserBot(models.Model):
    chat_id = models.IntegerField(primary_key=True)


class SymbolPairs(models.Model):
    symbol1 = models.CharField(max_length=15, null=False)
    symbol2 = models.CharField(max_length=15, null=False)
    interval = models.CharField(max_length=5, null=False)

    class Meta:
        unique_together = ('symbol1', 'symbol2', 'interval')


class UserPairs(models.Model):
    user_bot = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    symbol_pair = models.ForeignKey(SymbolPairs, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('user_bot', 'symbol_pair')