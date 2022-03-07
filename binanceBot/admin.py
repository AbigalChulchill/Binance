from django.contrib import admin
from binanceBot.models import UserBot, UserPairs, SymbolPairs
# Register your models here.


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'mode')


@admin.register(UserPairs)
class UserPairsAdmin(admin.ModelAdmin):
    ordering = ('symbol_pair', )
    list_display = ('user_bot', 'symbol_pair', 'status')


@admin.register(SymbolPairs)
class SymbolPairsAdmin(admin.ModelAdmin):
    list_display = ('symbol1', 'symbol2', 'interval', 'open_percent', 'close_percent')
