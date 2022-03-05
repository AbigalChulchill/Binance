from django.core.management.base import BaseCommand
from configparser import ConfigParser
from binanceBot.binanceAPI import Binance
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Command(BaseCommand):
    help = 'Start bot'

    def handle(self, *args, **options):
        config = ConfigParser()
        config.read('config.ini')

        bot_token = config['Bot']['token']

        updater = Updater(token=bot_token)

        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start_command))
        dispatcher.add_handler(CommandHandler('stat', statistic_command))

        updater.start_polling()
        updater.idle()


def start_command(update: Update, _: CallbackContext):
    update.effective_chat.send_message(text='Привет!')


def statistic_command(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()[1:]
    bnc = Binance()

    start_date = datetime(year=datetime.now().year,
                          month=datetime.now().month,
                          day=datetime.now().day,
                          hour=0, minute=0, second=0)

    start_date -= timedelta(days=7)

    end_date = datetime.now()

    symbol1 = data[0]
    symbol2 = data[1]
    interval = data[2]

    img, percent1, percent2, start_date, end_date = bnc.get_different(symbol1, symbol2, start_date, end_date, interval)

    different = int((percent1 - percent2) * 100) / 100
    caption = f'{symbol1} percent: {percent1}\n{symbol2} percent: {percent2}\n' \
              f'Different: {different}\n' \
              f'Date from:\t{start_date.strftime("%Y/%m/%d %H-%M-%S")}\n' \
              f'Date to:\t{end_date.strftime("%Y/%m/%d %H-%M-%S")}'

    update.effective_chat.send_photo(photo=open(img, 'rb'),
                                     caption=caption)
