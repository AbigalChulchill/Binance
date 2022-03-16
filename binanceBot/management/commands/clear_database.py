from django.core.management.base import BaseCommand
from binanceBot.models import Pair, UserBot, WhiteList, UserPair


class Command(BaseCommand):
    help = 'clear database'

    def handle(self, *args, **options):
        Pair.objects.all().delete()
        UserBot.objects.all().delete()
        WhiteList.objects.all().delete()
        UserPair.objects.all().delete()