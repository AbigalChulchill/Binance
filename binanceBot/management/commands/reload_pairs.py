from django.core.management.base import BaseCommand
from binanceBot.models import SymbolPairs, UserPairs, UserBot


class Command(BaseCommand):
    help = 'adding symbol pairs'

    def handle(self, *args, **options):
        SymbolPairs.objects.all().delete()
        UserPairs.objects.all().delete()
        pairs = ('ETHUSDT/ETCUSDT', 'ETHUSDT/BCHUSDT', 'ETHUSDT/LTCUSDT', 'ETHUSDT/BTCUSDT', 'BCHUSDT/LTCUSDT',
                 'BCHUSDT/ETCUSDT', 'ETCUSDT/LTCUSDT', 'BTCUSDT/ETCUSDT', 'BTCUSDT/BCHUSDT', 'BTCUSDT/LTCUSDT')

        intervals = ('3m', '5m')
        percents = ((3, 0.1), (5, 0.1))
        for i in intervals:
            for p in pairs:
                s1, s2 = p.split('/')
                s = SymbolPairs.objects.create(symbol1=s1, symbol2=s2, interval=i,
                                               open_percent=percents[intervals.index(i)][0],
                                               close_percent=percents[intervals.index(i)][1])
                s.save()

                for j in UserBot.objects.all():
                    UserPairs.objects.create(user_bot=j, symbol_pair=s).save()
