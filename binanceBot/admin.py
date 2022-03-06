from django.contrib import admin
from binanceBot.models import UserBot, UserPairs, SymbolPairs
# Register your models here.


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = ('chat_id', )


@admin.register(UserPairs)
class UserPairsAdmin(admin.ModelAdmin):
    list_display = ('user_bot', 'symbol_pair')


@admin.register(SymbolPairs)
class SymbolPairsAdmin(admin.ModelAdmin):
    list_display = ('symbol1', 'symbol2', 'interval', 'need_percent')
