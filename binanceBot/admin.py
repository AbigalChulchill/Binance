from django.contrib import admin
from binanceBot.models import UserBot, UserPair, SymbolPair, WhiteList
# Register your models here.


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'mode', 'active')


@admin.register(UserPair)
class UserPairsAdmin(admin.ModelAdmin):
    ordering = ('symbol_pair', )
    list_display = ('user_bot', 'symbol_pair', 'status')


@admin.register(SymbolPair)
class SymbolPairsAdmin(admin.ModelAdmin):
    list_display = ('symbol1', 'symbol2', 'interval', 'open_percent', 'close_percent')


@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('username', )
