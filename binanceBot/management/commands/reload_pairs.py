from django.core.management.base import BaseCommand
from binanceBot.models import SymbolPairs


class Command(BaseCommand):
    help = 'adding symbol pairs'

    def handle(self, *args, **options):
        SymbolPairs.objects.all().delete()
        pairs = ('ETHUSDT/ETCUSDT', 'ETHUSDT/BCHUSDT', 'ETHUSDT/LTCUSDT', 'ETHUSDT/BTCUSDT', 'BCHUSDT/LTCUSDT',
                 'BCHUSDT/ETCUSDT', 'ETCUSDT/LTCUSDT', 'BTCUSDT/ETCUSDT', 'BTCUSDT/BCHUSDT', 'BTCUSDT/LTCUSDT')

        intervals = ('3m', '5m', '15m')
        percents = (1, 3, 4)
        for i in intervals:
            for p in pairs:
                s1, s2 = p.split('/')

                SymbolPairs.objects.create(symbol1=s1, symbol2=s2, interval=i,
                                           need_percent=percents[intervals.index(i)]).save()

