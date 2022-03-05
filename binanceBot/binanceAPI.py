from binance import Client
from datetime import datetime
from datetime import timedelta
from matplotlib import pyplot as plt
import matplotlib
import pandas as pd


class Binance:
    def __init__(self):
        self.client = Client()

    def __get_data(self, symbol: str, interval: str) -> pd.DataFrame:
        data = self.client.get_klines(symbol=symbol, interval=interval)
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
                      interval: str, percentage_scale=True) -> tuple:
        data1 = self.__get_data(symbol1, interval)
        data2 = self.__get_data(symbol2, interval)

        if percentage_scale:
            data1 = Binance.__cost_to_percentage(data1, symbol1)
            data2 = Binance.__cost_to_percentage(data2, symbol2)

        matplotlib.use('agg')
        plt.plot(data1.index, data1[symbol1], label=symbol1)
        plt.plot(data2.index, data2[symbol2], label=symbol2)

        img_name = 'static/binanceBot/img/' + symbol1 + '-' + symbol2 + '.png'
        plt.legend()
        plt.savefig(img_name)

        plt.cla()

        return img_name, data1[symbol1][-1], data2[symbol2][-1], data1.index[0], data1.index[-1]
