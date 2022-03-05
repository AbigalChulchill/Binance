from django.contrib import admin
from binanceBot.models import UserBot, UserPairs, SymbolPairs
# Register your models here.


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    pass


@admin.register(UserPairs)
class UserPairsAdmin(admin.ModelAdmin):
    pass


@admin.register(SymbolPairs)
class SymbolPairsAdmin(admin.ModelAdmin):
    pass
