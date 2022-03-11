from django.contrib import admin
from binanceBot.models import UserBot, UserPair, SymbolPair, WhiteList
# Register your models here.


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'mode', 'default_deposit', 'active', 'auto_mode')


@admin.register(UserPair)
class UserPairsAdmin(admin.ModelAdmin):
    ordering = ('symbol_pair', )
    list_display = ('user_bot', 'symbol_pair', 'status', 'order_id_short', 'short', 'order_id_long', 'long')


@admin.register(SymbolPair)
class SymbolPairsAdmin(admin.ModelAdmin):
    list_display = ('symbol1', 'symbol2', 'interval', 'open_percent', 'close_percent')


@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('username', )
