import telegram.error
from django.core.management.base import BaseCommand
from django.conf import settings
from binanceBot.models import UserBot, UserPair, SymbolPair, WhiteList
from configparser import ConfigParser
from binanceBot.binanceAPI import Binance
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    Bot,
    ParseMode,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
)
import threading as th
import datetime
import time
import logging
import html
import json
import traceback

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

main_keyboard = ReplyKeyboardMarkup([
    ['Show open pairs'],
    ['LITE', 'HARD'],
], resize_keyboard=True)

BOT_RUNNING = True


class RepeatTimer(th.Timer):
    def run(self):
        while not self.finished.wait(self.interval) and BOT_RUNNING:
            self.function(*self.args, **self.kwargs)


def check_access_decorator(function):
    def wrapper(update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        chats = [i.chat_id for i in UserBot.objects.all()]

        result = None
        if chat_id not in chats or not UserBot.objects.get(chat_id=chat_id).active:
            update.effective_chat.send_message(text='Sorry, you don\'t have access')
        else:
            result = function(update, context)

        return result
    return wrapper


class Command(BaseCommand):
    help = 'Start bot'

    def handle(self, *args, **options):
        config = ConfigParser()
        config.read('config.ini')

        bot_token = config['Bot']['token']

        updater = Updater(token=bot_token)

        dispatcher = updater.dispatcher

        dispatcher.add_handler(MessageHandler(Filters.regex('Show open pairs'), show_open_pairs_command))
        dispatcher.add_handler(MessageHandler(Filters.regex('LITE'), set_lite_mode_command))
        dispatcher.add_handler(MessageHandler(Filters.regex('HARD'), set_hard_mode_command))

        dispatcher.add_handler(CommandHandler('start', start_command))
        dispatcher.add_handler(CommandHandler('stat', statistic_command))
        dispatcher.add_handler(CommandHandler('set_open', set_open_command))
        dispatcher.add_handler(CommandHandler('set_close', set_close_command))
        dispatcher.add_error_handler(error_handler)

        th.Thread(target=start_checking, args=(10, updater.bot)).start()
        updater.start_polling()
        updater.idle()

        global BOT_RUNNING
        BOT_RUNNING = False


def start_checking(interval: int, bot: Bot):
    while datetime.datetime.now().second % 10 != 0:
        time.sleep(1)

    RepeatTimer(interval, check_symbols, [bot]).start()
    logging.info('Check thread starting.')


def error_handler(update: object, context: CallbackContext) -> None:
    # logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    context.bot.send_message(chat_id=UserBot.objects.get(username='claudbros').chat_id,
                             text=message,
                             parse_mode=ParseMode.HTML)


def start_command(update: Update, _: CallbackContext):
    username, chat_id = update.effective_user.username, update.effective_chat.id

    white_list = [i.username for i in WhiteList.objects.all()]
    chats = [i.chat_id for i in UserBot.objects.all()]

    if username not in white_list and chat_id not in chats:
        update.effective_chat.send_message(text='Sorry, you don\'t have access')
        return None
    elif chat_id in chats and not UserBot.objects.get(chat_id=chat_id).active:
        update.effective_chat.send_message(text='Sorry, you don\'t have access')
        return None
    else:
        try:
            WhiteList.objects.get(username=username).delete()
        except WhiteList.DoesNotExist:
            pass

    try:
        user_bot = UserBot.objects.create(chat_id=chat_id, username=update.effective_user.username)
        user_bot.save()

        pairs = SymbolPair.objects.all()

        for pair in pairs:
            UserPair.objects.create(user_bot=user_bot, symbol_pair=pair, status='N').save()
    except Exception:
        user_bot = UserBot.objects.get(chat_id=chat_id)
        user_bot.username = update.effective_user.username
        user_bot.save()

        logging.info(f'user with {chat_id} already exists')

    update.effective_chat.send_message(text='Привет!', reply_markup=main_keyboard)
    logging.info(f'User {user_bot} log in')


@check_access_decorator
def set_lite_mode_command(update: Update, _: CallbackContext):
    user_bot = UserBot.objects.get(chat_id=update.effective_chat.id)
    user_bot.mode = 'L'
    user_bot.save()

    update.effective_chat.send_message(text='Current mode: Lite')


@check_access_decorator
def set_hard_mode_command(update: Update, _: CallbackContext):
    user_bot = UserBot.objects.get(chat_id=update.effective_chat.id)
    user_bot.mode = 'H'
    user_bot.save()

    update.effective_chat.send_message(text='Current mode: Hard')


@check_access_decorator
def set_close_command(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()[1:]

    interval = data[0]
    percent = float(data[1])

    for i in SymbolPair.objects.filter(interval=interval):
        i.close_percent = percent
        i.save()


@check_access_decorator
def set_open_command(update: Update, _: CallbackContext):

    data = update.effective_message.text.split()[1:]

    interval = data[0]
    percent = float(data[1])

    for i in SymbolPair.objects.filter(interval=interval):
        i.open_percent = percent
        i.save()


@check_access_decorator
def statistic_command(update: Update, _: CallbackContext):
    data = update.effective_message.text
    if len(data.split()) != 4:
        update.effective_chat.send_message(text='Example: /stat BTCUSDT LTCUSDT 3m')
        return

    data = data.split()[1:]
    bnc = Binance(test_net=settings.USE_TEST_NET)

    symbol1 = data[0]
    symbol2 = data[1]
    interval = data[2]

    try:
        img, percent1, percent2, start_date, end_date = bnc.get_different(symbol1, symbol2, interval, need_img=True)
        different = percent1 - percent2
        caption = f'{symbol1} percent: {round(percent1, 2)}\n' \
                  f'{symbol2} percent: {round(percent2, 2)}\n' \
                  f'Different: {round(different, 2)}\n' \
                  f'Date from:\t{start_date.strftime("%Y/%m/%d %H-%M-%S")}\n' \
                  f'Date to:\t{end_date.strftime("%Y/%m/%d %H-%M-%S")}'

        update.effective_chat.send_photo(photo=open(img, 'rb'),
                                         caption=caption)
    except Exception as e:
        update.effective_chat.send_message(text='Something went wrong: ' + str(e))


@check_access_decorator
def show_open_pairs_command(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id

    user_open_pairs = UserPair.objects.filter(status='O', user_bot=UserBot.objects.get(chat_id=chat_id))

    text = 'No open pairs' if len(user_open_pairs) == 0 else ''
    for p in user_open_pairs:
        text += f'{p.symbol_pair.symbol1}/{p.symbol_pair.symbol2} {p.symbol_pair.interval}\n'

    update.effective_chat.send_message(text=text)


def open_order(user_pair: UserPair, short: str, long: str):
    user = user_pair.user_bot

    bnc = Binance(api_key=user.api_key,
                  api_secret=user.api_secret,
                  test_net=settings.USE_TEST_NET)

    bnc.new_order(user_pair, short, long)

    logging.info(f'Create order for {user.username} on SHORT: {short} and LONG: {long}. Deposit {user.default_deposit}')


def open_users(bot: Bot, pair: SymbolPair, short: str, long: str, different: float):
    user_pairs = UserPair.objects.all().filter(symbol_pair=pair, status='N')

    for user in user_pairs:
        if not user.user_bot.active:
            continue

        if user.user_bot.mode == 'L' and user.symbol_pair.interval not in ('3m', ):
            continue

        if user.user_bot.mode == 'H' and user.symbol_pair.interval not in ('5m', ):
            continue

        try:
            if user.user_bot.auto_mode:
                th.Thread(target=open_order, args=(user, short, long)).start()
        except Exception as e:
            logging.info(str(e))
        else:
            chat_id = user.user_bot.chat_id
            user.status = 'O'
            user.save()

            send_signal(bot, chat_id, pair, short, long, different, 'Open')


def close_users(bot: Bot, pair: SymbolPair, short: str, long: str, different: float):
    user_pairs = UserPair.objects.all().filter(symbol_pair=pair, status='O')

    for user in user_pairs:
        if not user.user_bot.active:
            continue
        chat_id = user.user_bot.chat_id
        user.status = 'N'
        user.save()

        send_signal(bot, chat_id, pair, short, long, different, 'Close')


def send_signal(bot: Bot, chat_id: int, pair: SymbolPair,
                short: str, long: str, different: float,
                status: str):

    bot.send_message(chat_id=chat_id, text=f'STATUS: {status}.\n'
                                           f'Pair: {pair.symbol1}/{pair.symbol2}.\n'
                                           f'Short: {short}\n'
                                           f'Long: {long}\n'
                                           f'Spread: {different}.')

    logging.info(f'STATUS: {status}. {pair.symbol1}/{pair.symbol2} for {chat_id}')


def check_symbols(bot: Bot):
    logging.info('GETTING SYMBOLS')
    pairs = SymbolPair.objects.all()
    bnc = Binance(test_net=settings.USE_TEST_NET)

    for pair in pairs:
        per1, per2, start_date, end_date = bnc.get_different(pair.symbol1, pair.symbol2, pair.interval)

        different = round(per1 - per2, 2)
        logging.info(f'Get {pair.symbol1}/{pair.symbol2}({round(per1, 2)}/{round(per2, 2)}) '
                     f'in interval {pair.interval}. '
                     f'Different: {different}. Need for open: {pair.open_percent}. '
                     f'Need for close: {pair.close_percent}')

        short, long = (pair.symbol1, pair.symbol2) if per1 > per2 else (pair.symbol2, pair.symbol1)
        if abs(different) >= pair.open_percent:
            open_users(bot, pair, short, long, different)
        elif abs(different) <= pair.close_percent:
            close_users(bot, pair, short, long, different)
