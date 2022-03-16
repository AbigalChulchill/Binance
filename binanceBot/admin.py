from django.contrib import admin
from binanceBot.models import (
    UserBot,
    Pair,
    WhiteList,
    OpenPair,
    ConfirmationRequest,
    IgnorePair,
)
# Register your models here.


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'mode', 'deposit', 'active', 'auto_mode', 'open_percent', 'close_pnl')


@admin.register(Pair)
class SymbolPairsAdmin(admin.ModelAdmin):
    list_display = ('symbol1', 'symbol2', 'interval')


@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('username', )


@admin.register(OpenPair)
class OpenPairsAdmin(admin.ModelAdmin):
    list_display = ('user_bot', 'pair', 'deposit')


@admin.register(IgnorePair)
class IgnorePairAdmin(admin.ModelAdmin):
    list_display = ('user_bot', 'pair', 'ignore_start', 'ignore_time')


@admin.register(ConfirmationRequest)
class ConfirmationRequestAdmin(admin.ModelAdmin):
    list_display = ('user_bot', 'pair', 'short', 'long', 'deposit', 'create_datetime')