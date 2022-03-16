from django.core.management.base import BaseCommand
from binanceBot.models import Pair, ConfirmationRequest


class Command(BaseCommand):
    help = 'adding symbol pairs'

    def handle(self, *args, **options):
        ConfirmationRequest.objects.all().delete()
        Pair.objects.all().delete()

        pairs = ('ETHUSDT/ETCUSDT', 'ETHUSDT/BCHUSDT', 'ETHUSDT/LTCUSDT', 'ETHUSDT/BTCUSDT', 'BCHUSDT/LTCUSDT',
                 'BCHUSDT/ETCUSDT', 'ETCUSDT/LTCUSDT', 'BTCUSDT/ETCUSDT', 'BTCUSDT/BCHUSDT', 'BTCUSDT/LTCUSDT')

        intervals = ('3m', )
        for i in intervals:
            for p in pairs:
                s1, s2 = p.split('/')
                s = Pair.objects.create(symbol1=s1, symbol2=s2, interval=i)
                s.save()
