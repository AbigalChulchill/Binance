import django.utils.timezone
from django.core.management.base import BaseCommand
from django.conf import settings
from binanceBot.models import UserBot, Pair, WhiteList, OpenPair, ConfirmationRequest, IgnorePair
from configparser import ConfigParser
from binanceBot.binanceAPI import Binance
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Bot,
    ParseMode,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    Filters,
    CallbackQueryHandler,
)
import telegram.error
import threading as th
import datetime
import time
import logging
import html
import json
import traceback
import os
import signal

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

main_keyboard = ReplyKeyboardMarkup([
    ['Show open pairs', 'Show muted pairs', 'Change API key and API secret'],
    ['Settings']
], resize_keyboard=True)

BOT_RUNNING = True


class RepeatTimer(th.Timer):
    def run(self):
        while not self.finished.wait(self.interval) and BOT_RUNNING:
            try:
                self.function(*self.args, **self.kwargs)
            except Exception:
                logging.info('Error in thread')


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
        dispatcher.add_handler(MessageHandler(Filters.regex('Show muted pairs'), show_muted_pairs))
        dispatcher.add_handler(MessageHandler(Filters.regex('Settings'), settings_command))

        # dispatcher.add_handler(CommandHandler('start', start_command))
        dispatcher.add_handler(CommandHandler('stat', statistic_command))
        dispatcher.add_handler(CommandHandler('check_error', check_error_handler_command))
        dispatcher.add_handler(CommandHandler('open', open_pair_command))
        dispatcher.add_handler(CommandHandler('close', close_pair_command))
        dispatcher.add_handler(CommandHandler('pnl', change_pnl_command))
        dispatcher.add_handler(CommandHandler('deposit', change_deposit_command))

        dispatcher.add_handler(ConversationHandler(
            entry_points=[CommandHandler('start', start_command),
                          MessageHandler(Filters.regex('Change API key and API secret'), change_api_command)],
            states={
                1: [MessageHandler(Filters.text, get_api_command)],
                2: [MessageHandler(Filters.text, get_secret_command)],
            },
            fallbacks=[]
        ))

        updater.dispatcher.add_handler(CallbackQueryHandler(button))

        dispatcher.add_error_handler(error_handler)

        th.Thread(target=start_checking, args=(10, 3, updater.bot)).start()
        updater.start_polling()
        updater.idle()

        global BOT_RUNNING
        BOT_RUNNING = False


def start_checking(interval_open: int, interval_close: int, bot: Bot):
    while datetime.datetime.now().second % 10 != 0:
        time.sleep(1)

    RepeatTimer(interval_open, check_symbols_open, [bot]).start()
    RepeatTimer(60, check_ignore_pairs).start()
    RepeatTimer(60, check_confirmation_requests).start()
    RepeatTimer(interval_close, check_symbols_close, [bot]).start()

    logging.info('Check threads starting.')


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
    if len(message) >= 4096:
        with open('log_errors/log_error-' + str(datetime.datetime.now()) + '.txt', 'w') as f:
            f.write(message)
        message = message[:4096]

    try:
        context.bot.send_message(chat_id=UserBot.objects.get(username='claudbros').chat_id,
                                 text=message,
                                 parse_mode=ParseMode.HTML)
    except Exception:
        context.bot.send_message(chat_id=UserBot.objects.get(username='claudbros').chat_id,
                                 text=message)

    os.kill(os.getpid(), signal.SIGINT)


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
    except Exception:
        user_bot = UserBot.objects.get(chat_id=chat_id)
        user_bot.username = update.effective_user.username
        user_bot.save()

        logging.info(f'user with {chat_id} already exists')

    update.effective_chat.send_message(text='Hello!')
    logging.info(f'User {user_bot} log in')

    if not user_bot.api_key or not user_bot.api_secret:
        user_bot.active = False
        user_bot.save()

        update.effective_chat.send_message(text='Send API key, please', reply_markup=ReplyKeyboardRemove())
        return 1
    else:
        return ConversationHandler.END


@check_access_decorator
def change_api_command(update: Update, _: CallbackContext):
    user = UserBot.objects.get(chat_id=update.effective_chat.id)
    user.active = False
    user.save()

    update.effective_chat.send_message(text='Send API key, please')
    return 1


def get_api_command(update: Update, _: CallbackContext):
    user = UserBot.objects.get(chat_id=update.effective_chat.id)
    user.api_key = update.effective_message.text
    user.save()

    update.effective_chat.send_message(text='Send API secret, please')
    return 2


def get_secret_command(update: Update, _: CallbackContext):
    user = UserBot.objects.get(chat_id=update.effective_chat.id)
    user.api_secret = update.effective_message.text
    user.save()

    bnc = Binance(api_key=user.api_key,
                  api_secret=user.api_secret,
                  test_net=settings.USE_TEST_NET)

    try:
        bnc.futures.account()
    except Exception:
        update.effective_chat.send_message(text='Invalid API key or API secret. Please, try again')
        return 1

    user.active = True
    user.save()

    update.effective_chat.send_message(text='OK', reply_markup=main_keyboard)
    return ConversationHandler.END


@check_access_decorator
def statistic_command(update: Update, _: CallbackContext):
    data = update.effective_message.text
    if len(data.split()) != 4:
        update.effective_chat.send_message(text='Example: /stat BTCUSDT LTCUSDT 3m')
        return

    data = data.split()
    send_plot(update, data[1], data[2], data[3])


@check_access_decorator
def show_open_pairs_command(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id

    user_open_pairs = OpenPair.objects.filter(user_bot=UserBot.objects.get(chat_id=chat_id))

    text = 'No open pairs' if len(user_open_pairs) == 0 else 'Open pairs:\nClick for plot'

    inline_keyboard = []
    for p in user_open_pairs:
        inline_keyboard.append(
            [InlineKeyboardButton(f'{p.pair.symbol1}/{p.pair.symbol2} {p.pair.interval}.',
                                  callback_data=f'PLOT-{p.pair.symbol1} {p.pair.symbol2} {p.pair.interval}')]
        )

    update.effective_chat.send_message(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@check_access_decorator
def show_muted_pairs(update: Update, _: CallbackContext):
    if len(IgnorePair.objects.filter(user_bot=UserBot.objects.get(chat_id=update.effective_chat.id))) == 0:
        update.effective_chat.send_message(text='No muted pairs')
    else:
        update.effective_chat.send_message(text='Muted pairs:\nClick for unmute.',
                                           reply_markup=get_muted_inline_markup(update.effective_chat.id))


@check_access_decorator
def open_pair_command(update: Update, context: CallbackContext):
    data = update.effective_message.text

    if len(data.split()) != 4:
        update.effective_chat.send_message(text='Example: /open BTCUSDT LTCUSDT 3m')
        return

    data = data.split()[1:]

    user = UserBot.objects.get(chat_id=update.effective_chat.id)
    open_pairs = OpenPair.objects.filter(user_bot=user)
    if len(open_pairs) != 0:
        update.effective_chat.send_message(text='You already have an open pair.')
        return

    bnc = Binance(api_key=user.api_key,
                  api_secret=user.api_secret,
                  test_net=settings.USE_TEST_NET)

    pair = Pair.objects.get(symbol1=data[0], symbol2=data[1], interval=data[2])
    per1, per2, start_date, end_date = bnc.get_different(pair.symbol1, pair.symbol2, pair.interval)

    short, long = (pair.symbol1, pair.symbol2) if per1 > per2 else (pair.symbol2, pair.symbol1)
    if not open_order(context.bot, user, pair, short, long):
        update.effective_chat.send_message(text='Something went wrong.')
    else:
        update.effective_chat.send_message(text=f'{pair} opened.')


@check_access_decorator
def close_pair_command(update: Update, _: CallbackContext):
    try:
        user = UserBot.objects.get(chat_id=update.effective_chat.id)
        open_pair = OpenPair.objects.get(user_bot=user)
        pnl = get_pnl(open_pair)
        close_pair(open_pair)

        update.effective_chat.send_message(text=f'{open_pair.pair} closed. PNL: {pnl}')
        open_pair.delete()

    except OpenPair.DoesNotExist:
        update.effective_chat.send_message(text='No open pairs.')
    except Exception:
        update.effective_chat.send_message(text='Something went wrong')


@check_access_decorator
def settings_command(update: Update, _: CallbackContext):
    update.effective_chat.send_message(
        text='Settings',
        reply_markup=get_settings_inline(update.effective_chat.id))


@check_access_decorator
def change_pnl_command(update: Update, _: CallbackContext):
    data = update.effective_message.text

    if len(data.split()) != 2:
        update.effective_chat.send_message(text='Example: /pnl 1')
        return

    pnl_percent = float(data.split()[1])
    user = UserBot.objects.get(chat_id=update.effective_chat.id)

    user.close_pnl = pnl_percent
    user.save()

    update.effective_chat.send_message('Pnl changed.')


@check_access_decorator
def change_deposit_command(update: Update, _: CallbackContext):
    user = UserBot.objects.get(chat_id=update.effective_chat.id)
    if len(OpenPair.objects.filter(user_bot=user)) != 0:
        update.effective_chat.send_message(text='Close the open pairs')
        return

    data = update.effective_message.text
    if len(data.split()) != 2:
        update.effective_chat.send_message(text='Example: /deposit 10000')
        return

    deposit = float(data.split()[1])
    user = UserBot.objects.get(chat_id=update.effective_chat.id)

    user.deposit = deposit
    user.save()

    update.effective_chat.send_message('Deposit changed.')


def check_error_handler_command(update: Update, _: CallbackContext):
    raise telegram.error.NetworkError('Test error ' + str(update.effective_chat.id))


def get_settings_inline(chat_id: int):
    user = UserBot.objects.get(chat_id=chat_id)

    mode = 'Mode: ' + user.mode
    auto_mode = 'Auto: ' + str(user.auto_mode)

    inline_keyboard = [
        [InlineKeyboardButton(mode, callback_data=f'MODE-{user.mode} {user.chat_id}')],
        [InlineKeyboardButton(auto_mode, callback_data=f'AUTO-{user.auto_mode} {user.chat_id}')]
    ]

    return InlineKeyboardMarkup(inline_keyboard)


def get_muted_inline_markup(chat_id: int):
    ignore_pairs = IgnorePair.objects.filter(user_bot=UserBot.objects.get(chat_id=chat_id))

    inline_keyboard = []
    for p in ignore_pairs:
        inline_keyboard.append(
            [InlineKeyboardButton(f'{p.pair.symbol1}/{p.pair.symbol2} {p.pair.interval}.',
                                  callback_data=f'UNMUTE-{p.id}')]
        )

    return InlineKeyboardMarkup(inline_keyboard)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split('-')

    if data[0] == 'PLOT':
        data = data[1].split()
        send_plot(update, data[0], data[1], data[2])
    elif data[0] == 'UNMUTE':
        IgnorePair.objects.get(id=int(data[1])).delete()

        query.edit_message_text(text='Muted pairs:\nClick for unmute.',
                                reply_markup=get_muted_inline_markup(update.effective_chat.id))
    elif data[0] == 'MODE' or data[0] == 'AUTO':
        chat_id = int(data[1].split()[1])
        user = UserBot.objects.get(chat_id=chat_id)

        if data[0] == 'MODE':
            user.mode = 'H' if data[1].split()[0] == 'L' else 'L'
        else:
            user.auto_mode = not data[1].split()[0] == 'True'
        user.save()
        query.edit_message_reply_markup(reply_markup=get_settings_inline(chat_id))
    else:
        request_id = int(data[1].split()[0])
        try:
            request = ConfirmationRequest.objects.get(id=request_id)
        except ConfirmationRequest.DoesNotExist:
            query.edit_message_text(text='The signal is outdated')
            return

        if data[0] == 'OPEN':
            open_pairs = OpenPair.objects.filter(user_bot=request.user_bot)
            if len(open_pairs) != 0:
                query.edit_message_text(text='You already have an open pair')
            if open_order(context.bot, request.user_bot, request.pair, request.short, request.long):
                query.edit_message_text(text=f'{request.pair} opened.')
            else:
                query.edit_message_text(text=f'something went wrong.')
        elif data[0] == 'MUTE':
            ignore_time = int(data[1].split()[1])

            if len(IgnorePair.objects.filter(user_bot=request.user_bot, pair=request.pair)) != 0:
                query.edit_message_text(text=f'{request.pair} already muted')
            else:
                IgnorePair.objects.create(user_bot=request.user_bot, pair=request.pair, ignore_time=ignore_time).save()
                logging.info(f'{request.user_bot} mute fore {request.pair} pair')

                query.edit_message_text(text=f'{request.pair} mute fore {ignore_time // 3600} hours')

            request.delete()


def send_plot(update: Update,  symbol1: str, symbol2: str, interval: str):
    bnc = Binance(test_net=settings.USE_TEST_NET)
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


def open_order(bot: Bot, user: UserBot, pair: Pair, short: str, long: str, user_open_pair=None):
    try:
        if not user_open_pair:
            user_open_pair = [i.pair for i in OpenPair.objects.filter(user_bot=user)]

        if len(user_open_pair) != 0:
            return False

        bnc = Binance(api_key=user.api_key,
                      api_secret=user.api_secret,
                      test_net=settings.USE_TEST_NET)

        bnc.new_order(user.deposit / 2, short, long)

        OpenPair.objects.create(user_bot=user, pair=pair, short=short, long=long, deposit=user.deposit).save()

        logging.info(f'Create order for {user.username} on SHORT: {short} and LONG: {long}. '
                     f'Deposit {user.deposit}')

        bot.send_message(chat_id=user.chat_id, text=f'Create order for {user.username} on '
                                                    f'SHORT: {short} and LONG: {long}. Deposit {user.deposit}')
        return True
    except Exception as e:
        logging.info(f'Error in creating order for {user.username}. Error: {e}')
        print(e)
        return False


def send_open_order_message(bot: Bot, user: UserBot, pair: Pair, short: str, long: str, different: float):
    text = f'Pair: {pair.symbol1}/{pair.symbol2}.\n' \
           f'Short: {short}\n' \
           f'Long: {long}\n' \
           f'Spread: {different}.\n'

    request = ConfirmationRequest.objects.create(user_bot=user, pair=pair, short=short, long=long,
                                                 deposit=user.deposit, text=text)
    request.save()

    open_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Open?", callback_data=f'OPEN-{str(request.id)}')],
        [InlineKeyboardButton('Mute 1 hour', callback_data=f'MUTE-{str(request.id)} {3600}')],
        [InlineKeyboardButton('Mute 3 hours', callback_data=f'MUTE-{str(request.id)} {3600 * 3}')],
        [InlineKeyboardButton('Mute 24 hours', callback_data=f'MUTE-{str(request.id)} {3600 * 24}')],
    ])

    bot.send_message(chat_id=user.chat_id, text=text, reply_markup=open_keyboard)


def open_users(bot: Bot, pair: Pair, short: str, long: str, different: float):
    users = UserBot.objects.all().filter(active=True)

    for user in users:
        user_wait_list = [i.pair for i in ConfirmationRequest.objects.filter(user_bot=user)]
        user_ignore_pair = [i.pair for i in IgnorePair.objects.filter(user_bot=user)]
        user_open_pair = [i.pair for i in OpenPair.objects.filter(user_bot=user)]

        if pair in user_wait_list or pair in user_ignore_pair or pair in user_open_pair:
            continue

        if user.mode == 'L' and pair.interval not in ('3m', ):
            continue

        if user.mode == 'H' and pair.interval not in ('5m', ):
            continue

        open_percent = user.open_percent
        if abs(different) >= open_percent:
            if not user.auto_mode:
                send_open_order_message(bot, user, pair, short, long, different)
            else:
                open_order(bot, user, pair, short, long, user_open_pair=user_open_pair)


def check_symbols_open(bot: Bot):
    logging.info('GETTING PAIRS')
    pairs = Pair.objects.all()
    bnc = Binance(test_net=settings.USE_TEST_NET)

    for pair in pairs:
        per1, per2, start_date, end_date = bnc.get_different(pair.symbol1, pair.symbol2, pair.interval)

        different = round(per1 - per2, 2)
        logging.info(f'Get {pair.symbol1}/{pair.symbol2}({round(per1, 2)}/{round(per2, 2)}) '
                     f'in interval {pair.interval}. '
                     f'Different: {different}')

        short, long = (pair.symbol1, pair.symbol2) if per1 > per2 else (pair.symbol2, pair.symbol1)

        open_users(bot, pair, short, long, different)


def get_pnl(pair: OpenPair):
    user = pair.user_bot
    bnc = Binance(api_key=user.api_key,
                  api_secret=user.api_secret,
                  test_net=settings.USE_TEST_NET)

    return bnc.get_pnl_sum(pair.short, pair.long)


def close_pair(pair: OpenPair):
    user = pair.user_bot
    bnc = Binance(api_key=user.api_key,
                  api_secret=user.api_secret,
                  test_net=settings.USE_TEST_NET)

    th.Thread(target=bnc.close_order, args=(pair.short, pair.long)).start()


def check_symbols_close(bot: Bot):
    logging.info('CLOSING PAIRS')

    open_pairs = OpenPair.objects.all()
    if len(open_pairs) == 0:
        logging.info("Nothing to close.")

    for pair in open_pairs:
        user = pair.user_bot

        try:
            pnl = get_pnl(pair)
        except Exception:
            logging.info(f'Can\'t get pnl for {pair}. User {user.username}')
        else:
            logging.info(f'User: {user.username}. Pair: {pair.pair}. Deposit: {pair.deposit}. Pnl: {pnl}. '
                         f'Need for close {pair.deposit * (user.close_pnl / 100)}')

            if pnl >= pair.deposit * (user.close_pnl / 100):
                try:
                    close_pair(pair)
                    bot.send_message(chat_id=user.chat_id, text=f'{pair.pair} closed. PNL: {pnl}')
                    pair.delete()
                    logging.info(f'CLOSED. User: {user.username}. Pair: {pair.pair}. '
                                 f'Deposit: {pair.deposit}. Pnl: {pnl}')
                except Exception:
                    logging.info(f'Can\'t close {pair}. User {user.username}')


def check_confirmation_requests():
    for request in ConfirmationRequest.objects.all():
        if (django.utils.timezone.now() - request.create_datetime).seconds >= 180:
            request.delete()


def check_ignore_pairs():
    for pair in IgnorePair.objects.all():
        if (django.utils.timezone.now() - pair.ignore_start).seconds >= pair.ignore_time:
            pair.delete()
