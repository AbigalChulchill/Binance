from django.core.management.base import BaseCommand
from binanceBot.models import UserBot, UserPairs, SymbolPairs
from configparser import ConfigParser
from binanceBot.binanceAPI import Binance
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    Bot,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
)
import threading as th
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

main_keyboard = ReplyKeyboardMarkup([
    ['Show open pairs'],
    ['LITE', 'HARD'],
], resize_keyboard=True)


class RepeatTimer(th.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Command(BaseCommand):
    help = 'Start bot'

    def handle(self, *args, **options):
        config = ConfigParser()
        config.read('config.ini')

        bot_token = config['Bot']['token2']

        updater = Updater(token=bot_token)

        dispatcher = updater.dispatcher

        dispatcher.add_handler(MessageHandler(Filters.regex('Show open pairs'), show_open_pairs_command))
        dispatcher.add_handler(MessageHandler(Filters.regex('LITE'), set_lite_mode_command))
        dispatcher.add_handler(MessageHandler(Filters.regex('HARD'), set_hard_mode_command))

        dispatcher.add_handler(CommandHandler('start', start_command))
        dispatcher.add_handler(CommandHandler('stat', statistic_command))
        dispatcher.add_handler(CommandHandler('set_open', set_open_command))
        dispatcher.add_handler(CommandHandler('set_close', set_close_command))

        RepeatTimer(58, check_symbols, [updater.bot]).start()
        updater.start_polling()
        updater.idle()


def start_command(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id
    try:
        user_bot = UserBot.objects.create(chat_id=chat_id, username=update.effective_user.username)
        user_bot.save()

        pairs = SymbolPairs.objects.all()

        for pair in pairs:
            UserPairs.objects.create(user_bot=user_bot, symbol_pair=pair, status='N').save()
    except Exception:
        user_bot = UserBot.objects.get(chat_id=chat_id)
        user_bot.username = update.effective_user.username
        user_bot.save()

        logging.info(f'user with {chat_id} already exists')

    update.effective_chat.send_message(text='Привет!', reply_markup=main_keyboard)
    logging.info(f'User {user_bot} log in')


def set_lite_mode_command(update: Update, _: CallbackContext):
    user_bot = UserBot.objects.get(chat_id=update.effective_chat.id)
    user_bot.mode = 'L'
    user_bot.save()

    update.effective_chat.send_message(text='Current mode: Lite')


def set_hard_mode_command(update: Update, _: CallbackContext):
    user_bot = UserBot.objects.get(chat_id=update.effective_chat.id)
    user_bot.mode = 'H'
    user_bot.save()

    update.effective_chat.send_message(text='Current mode: Hard')


def set_close_command(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()[1:]

    interval = data[0]
    percent = float(data[1])

    for i in SymbolPairs.objects.filter(interval=interval):
        i.close_percent = percent
        i.save()


def set_open_command(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()[1:]

    interval = data[0]
    percent = float(data[1])

    for i in SymbolPairs.objects.filter(interval=interval):
        i.open_percent = percent
        i.save()


def statistic_command(update: Update, _: CallbackContext):
    data = update.effective_message.text
    if len(data.split()) != 4:
        update.effective_chat.send_message(text='Example: /stat BTCUSDT LTCUSDT 3m')
        return

    data = data.split()[1:]
    bnc = Binance()

    symbol1 = data[0]
    symbol2 = data[1]
    interval = data[2]

    try:
        img, percent1, percent2, start_date, end_date = bnc.get_different(symbol1, symbol2, interval)
        different = int((percent1 - percent2) * 100) / 100
        caption = f'{symbol1} percent: {percent1}\n' \
                  f'{symbol2} percent: {percent2}\n' \
                  f'Different: {different}\n' \
                  f'Date from:\t{start_date.strftime("%Y/%m/%d %H-%M-%S")}\n' \
                  f'Date to:\t{end_date.strftime("%Y/%m/%d %H-%M-%S")}'

        update.effective_chat.send_photo(photo=open(img, 'rb'),
                                         caption=caption)
    except Exception:
        update.effective_chat.send_message(text='Something went wrong')


def show_open_pairs_command(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id

    user_open_pairs = UserPairs.objects.filter(status='O', user_bot=UserBot.objects.get(chat_id=chat_id))

    text = 'No open pairs' if len(user_open_pairs) == 0 else ''
    for p in user_open_pairs:
        text += f'{p.symbol_pair.symbol1}/{p.symbol_pair.symbol2} {p.symbol_pair.interval}\n'

    update.effective_chat.send_message(text=text)


def open_users(bot: Bot, pair: SymbolPairs, short: str, long: str, different: float, img: str):
    user_pairs = UserPairs.objects.all().filter(symbol_pair=pair, status='N')

    for user in user_pairs:
        if user.user_bot.mode == 'L' and user.symbol_pair.interval not in ('3m', ):
            continue

        chat_id = user.user_bot.chat_id
        user.status = 'O'
        user.save()

        send_signal(bot, chat_id, pair, short, long, different, img, 'Open')


def close_users(bot: Bot, pair: SymbolPairs, short: str, long: str, different: float, img: str):
    user_pairs = UserPairs.objects.all().filter(symbol_pair=pair, status='O')

    for user in user_pairs:
        chat_id = user.user_bot.chat_id
        user.status = 'N'
        user.save()

        send_signal(bot, chat_id, pair, short, long, different, img, 'Close')


def send_signal(bot: Bot, chat_id: int, pair: SymbolPairs,
                short: str, long: str, different: float,
                img: str, status: str):

    bot.send_message(chat_id=chat_id, text=f'STATUS: {status}.\n'
                                           f'Pair: {pair.symbol1}/{pair.symbol2} {pair.interval}.\n'
                                           f'Short: {short}\n'
                                           f'Long: {long}\n'
                                           f'Spread: {different}.')

    logging.info(f'STATUS: {status}. {pair.symbol1}/{pair.symbol2} for {chat_id}')


def check_symbols(bot: Bot):
    logging.info('GETTING SYMBOLS')
    pairs = SymbolPairs.objects.all()
    bnc = Binance()

    for pair in pairs:
        img, per1, per2, start_date, end_date = bnc.get_different(pair.symbol1, pair.symbol2, pair.interval)

        different = int((per1 - per2) * 100) / 100
        logging.info(f'Get {pair.symbol1}/{pair.symbol2} in interval {pair.interval}. '
                     f'Different: {different}. Need for open: {pair.open_percent}. '
                     f'Need for close: {pair.close_percent}')

        short, long = (pair.symbol1, pair.symbol2) if per1 > per2 else (pair.symbol2, pair.symbol1)
        if abs(different) >= pair.open_percent:
            open_users(bot, pair, short, long, different, img)
        elif abs(different) <= pair.close_percent:
            close_users(bot, pair, short, long, different, img)
