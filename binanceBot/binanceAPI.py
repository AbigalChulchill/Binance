from binance.spot import Spot
from binance.futures import Futures
from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib
import pandas as pd
from binanceBot.models import UserBot, UserPair


class Binance:
    def __init__(self, api_key=None, api_secret=None, test_net=False):
        if not api_key and not api_secret:
            self.client = Spot()
            self.futures = Futures()
        else:
            self.client = Spot(key=api_key, secret=api_secret)
            self.futures = Futures(key=api_key, secret=api_secret)

        if test_net:
            self.client.base_url = 'https://testnet.binance.vision'
            self.futures.base_url = 'https://testnet.binancefuture.com'

    def __get_data(self, symbol: str, interval: str) -> pd.DataFrame:

        data = self.futures.klines(symbol, interval)
        for i in range(len(data)):
            data[i][0] = data[i][0] // 1000
            data[i][0] = datetime.fromtimestamp(data[i][0])
            data[i] = [data[i][0], float(data[i][4])]

        data_frame = pd.DataFrame(data)
        data_frame.columns = ['date', symbol]
        data_frame['date'] = pd.to_datetime(data_frame['date'], unit='s')
        data_frame = data_frame.set_index('date')
        return data_frame

    @staticmethod
    def __cost_to_percentage(data: pd.DataFrame, symbol) -> pd.DataFrame:
        data_copy = data.copy()
        init_value = data_copy[symbol][0]
        data_copy[symbol] = (data_copy[symbol] - init_value) / init_value * 100

        return data_copy

    def get_different(self, symbol1: str, symbol2: str,
                      interval: str, percentage_scale=True, need_img=False) -> tuple:
        data1 = self.__get_data(symbol1, interval)
        data2 = self.__get_data(symbol2, interval)

        if percentage_scale:
            data1 = Binance.__cost_to_percentage(data1, symbol1)
            data2 = Binance.__cost_to_percentage(data2, symbol2)

        if need_img:
            matplotlib.use('agg')
            plt.plot(data1.index, data1[symbol1], label=symbol1)
            plt.plot(data2.index, data2[symbol2], label=symbol2)

            img_name = 'static/binanceBot/img/' + symbol1 + '-' + symbol2 + '-' + interval + '.png'
            plt.legend()
            plt.savefig(img_name)

            plt.cla()

            return img_name, data1[symbol1][-1], data2[symbol2][-1], data1.index[0], data1.index[-1]
        return data1[symbol1][-1], data2[symbol2][-1], data1.index[0], data1.index[-1]

    def new_order(self, user_pair: UserPair, short: str, long: str):
        user = user_pair.user_bot
        short_price = float(self.futures.ticker_price(short)['price'])
        long_price = float(self.futures.ticker_price(long)['price'])

        deposit = user.default_deposit

        info = self.futures.exchange_info()
        short_precision = None
        long_precision = None

        for x in info['symbols']:
            if x['symbol'] == short:
                short_precision = int(x['quantityPrecision'])
            if x['symbol'] == long:
                long_precision = int(x['quantityPrecision'])

        quantity_short = round((deposit / 2) / short_price, short_precision)
        quantity_long = round((deposit / 2) / long_price, long_precision)

        self.futures.change_leverage(symbol=short, leverage=1)
        self.futures.change_leverage(symbol=long, leverage=1)

        try:
            self.futures.change_margin_type(symbol=short, marginType='CROSSED')
            self.futures.change_margin_type(symbol=long, marginType='CROSSED')
        except Exception:
            pass

        response_short = self.futures.new_order(symbol=short, side='SELL', type='MARKET', quantity=quantity_short)
        response_long = self.futures.new_order(symbol=long, side='BUY', type='MARKET', quantity=quantity_long)

        user_pair.order_id_short = int(response_short['orderId'])
        user_pair.short = short

        user_pair.order_id_long = int(response_long['orderId'])
        user_pair.long = long

        user_pair.save()
