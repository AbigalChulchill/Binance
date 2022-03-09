from django.core.management.base import BaseCommand
from binanceBot.models import SymbolPair


class Command(BaseCommand):
    help = 'adding symbol pairs'

    def handle(self, *args, **options):
        SymbolPair.objects.all().delete()

        pairs = ('ETHUSDT/ETCUSDT', 'ETHUSDT/BCHUSDT', 'ETHUSDT/LTCUSDT', 'ETHUSDT/BTCUSDT', 'BCHUSDT/LTCUSDT',
                 'BCHUSDT/ETCUSDT', 'ETCUSDT/LTCUSDT', 'BTCUSDT/ETCUSDT', 'BTCUSDT/BCHUSDT', 'BTCUSDT/LTCUSDT')

        for p in pairs:
            s1, s2 = p.split('/')
            s = SymbolPair.objects.create(symbol1=s1, symbol2=s2, interval='3m',
                                          open_percent=3.0,
                                          close_percent=0.1)
            s.save()
