from django.core.management.base import BaseCommand
from binanceBot.models import UserBot, UserPairs, SymbolPairs
from configparser import ConfigParser
from binanceBot.binanceAPI import Binance
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Bot,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
)
import threading as th
import time
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

main_keyboard = ReplyKeyboardMarkup([
    ['Редактировать пары'],
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

        dispatcher.add_handler(CommandHandler('start', start_command))
        dispatcher.add_handler(CommandHandler('stat', statistic_command))
        dispatcher.add_handler(MessageHandler(Filters.regex('Редактировать пары'), redact_pairs_command))
        dispatcher.add_handler(CallbackQueryHandler(button))

        RepeatTimer(58, send_graphs, [updater.bot, False]).start()
        updater.start_polling()
        updater.idle()


def start_command(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id

    try:
        user_bot = UserBot.objects.create(chat_id=chat_id)
        user_bot.save()
    except Exception:
        logging.info(f'user with {chat_id} already exists')
    finally:
        update.effective_chat.send_message(text='Привет!', reply_markup=main_keyboard)


def statistic_command(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()[1:]
    bnc = Binance()

    symbol1 = data[0]
    symbol2 = data[1]
    interval = data[2]

    img, percent1, percent2, start_date, end_date = bnc.get_different(symbol1, symbol2, interval)

    different = int((percent1 - percent2) * 100) / 100
    caption = f'{symbol1} percent: {percent1}\n{symbol2} percent: {percent2}\n' \
              f'Different: {different}\n' \
              f'Date from:\t{start_date.strftime("%Y/%m/%d %H-%M-%S")}\n' \
              f'Date to:\t{end_date.strftime("%Y/%m/%d %H-%M-%S")}'

    update.effective_chat.send_photo(photo=open(img, 'rb'),
                                     caption=caption)


def generate_inline_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    pairs = SymbolPairs.objects.all()
    user_pairs = [i.symbol_pair for i in UserPairs.objects.all().filter(user_bot=UserBot.objects.get(chat_id=chat_id))]
    buttons = list()

    for i in pairs:
        callback_data = {'chat_id': chat_id, 'pair_id': i.id}
        text = f'{i.symbol1} / {i.symbol2} {i.interval}'
        if i in user_pairs:
            callback_data['sub'] = True
            text += ' - Отписаться'
        else:
            callback_data['sub'] = False
            text += ' - Подписаться'

        buttons.append([InlineKeyboardButton(text, callback_data=json.dumps(callback_data))])

    return InlineKeyboardMarkup(buttons)


def redact_pairs_command(update: Update, _: CallbackContext):
    update.effective_chat.send_message(text='Настройка',
                                       reply_markup=generate_inline_keyboard(update.effective_chat.id))


def button(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    data = json.loads(query.data)

    if not data['sub']:
        user_pair = UserPairs.objects.create(user_bot=UserBot.objects.get(chat_id=data['chat_id']),
                                             symbol_pair=SymbolPairs.objects.get(id=data['pair_id']))
        user_pair.save()
    else:
        user_pair = UserPairs.objects.get(user_bot=UserBot.objects.get(chat_id=data['chat_id']),
                                          symbol_pair=SymbolPairs.objects.get(id=data['pair_id']))
        user_pair.delete()

    query.edit_message_text('Настройка',
                            reply_markup=generate_inline_keyboard(update.effective_chat.id))


def send_graphs(bot: Bot, send_date: bool):
    symbol_pairs = SymbolPairs.objects.all()

    user_pairs = UserPairs.objects.all()
    if len(user_pairs) == 0:
        logging.info('nothing to send')
        return

    bnc = Binance()
    graphs = dict()
    for i in symbol_pairs:
        img, percent1, percent2, start_date, end_date = bnc.get_different(i.symbol1, i.symbol2, i.interval)

        different = int((percent1 - percent2) * 100) / 100
        logging.info(f'Get {i.symbol1}/{i.symbol2} in interval {i.interval}. '
                     f'Different: {different}. Need: {i.need_percent}')

        if abs(different) < i.need_percent:
            continue

        graphs[i.id] = {i.symbol1: percent1, i.symbol2: percent2,
                        'different': different, 'need_percent': i.need_percent}

        if send_date:
            graphs[i.id]['Start date'] = start_date.strftime("%Y/%m/%d %H-%M-%S")
            graphs[i.id]['End date'] = end_date.strftime("%Y/%m/%d %H-%M-%S")

        caption = ''

        for key in graphs[i.id]:
            caption += key + ': ' + str(graphs[i.id][key]) + '\n'

        graphs[i.id]['img'] = img
        graphs[i.id]['caption'] = caption

    for i in user_pairs:
        pair_id = i.symbol_pair.id
        if pair_id not in graphs:
            continue

        bot.send_photo(chat_id=i.user_bot.chat_id, photo=open(graphs[pair_id]['img'], 'rb'),
                       caption=graphs[pair_id]['caption'])
        logging.info(f'Send graph to {i.user_bot.chat_id}')




