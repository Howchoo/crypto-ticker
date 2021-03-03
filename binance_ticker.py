#!/usr/bin/env python3


from dotenv import load_dotenv
import requests
from frame import Frame
from rgbmatrix import graphics
import os
import itertools
import time
import logging
import sys

class BinanceTicker(Frame):
    def __init__(self, *args, **kwargs):
        load_dotenv()
        self._last_fetch_time = 0
        self.refresh_rate = int(os.environ.get('REFRESH_RATE', 15))  # 300s or 5m
        self.sleep = int(os.environ.get('SLEEP', 5))  # 3s
        self.symbols = os.getenv('SYMBOLS', 'btc,bnb,ada')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self._cached_price_map = None

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        super().__init__(*args, **kwargs)

    @property
    def price_map(self):
        # Determine if the cache is stale
        cache_is_stale = (time.time() - self._last_fetch_time) > self.refresh_rate

        # See if we should return the cached price data
        if self._cached_price_map and not cache_is_stale:
            self.logger.info('Using cached price map.')
            return self._cached_price_map

        # Otherwise fetch new data and set the _last_fetch_time
        price_map = self.get_24hour_change()
        self._last_fetch_time = time.time()
        self._cached_price_map = price_map

        return price_map

    def get_24hour_change(self):
        data = {}
        BASE_URL='https://api.binance.com/'

        for symbol in self.symbols.split(','):
            response = requests.get(f'{BASE_URL}api/v3/ticker/24hr?symbol={symbol.upper()}BUSD')
            data[symbol] = response.json()
        
        return data
        
    def get_ticker_canvas(self, key):
        symbol = self.price_map[key]
        canvas = self.matrix.CreateFrameCanvas()
        canvas.Clear()

        font_symbol = graphics.Font()
        font_symbol.LoadFont('fonts/7x13.bdf')

        font_price = graphics.Font()
        font_price.LoadFont('fonts/6x12.bdf')

        font_change = graphics.Font()
        font_change.LoadFont('fonts/6x10.bdf')

        change_width = sum(
            [font_change.CharacterWidth(ord(c)) for c in f'${symbol["priceChangePercent"]:.2f}']
        )
        change_x = 62 - change_width

        # Get colors
        main_color = graphics.Color(255, 255, 0)
        change_color = (
            graphics.Color(194, 24, 7)
            if symbol['priceChangePercent'].startswith('-')
            else graphics.Color(46, 139, 87)
        )

        # Draw the elements on the canvas
        graphics.DrawText(canvas, font_symbol, 3, 12, main_color, key)
        graphics.DrawText(canvas, font_price, 3, 28, main_color, symbol['weightedAvgPrice'])
        graphics.DrawText(
            canvas, font_change, change_x, 10, change_color, symbol['priceChangePercent']
        )

        return canvas

    def get_error_canvas(self):
        canvas = self.matrix.CreateFrameCanvas()
        canvas.Clear()
        font = graphics.Font()
        font.LoadFont('../rpi-rgb-led-matrix/fonts/7x13.bdf')
        color = graphics.Color(194, 24, 7)
        graphics.DrawText(canvas, font, 15, 20, color, 'ERROR')
        return canvas

    def get_symbols(self):
        price_map_length = len(self.price_map)
        keys = list(self.price_map.keys())
        self.logger.info(keys, keys)

        for index in itertools.cycle(range(price_map_length)):
            self.logger.info('using index', index)
            try:
                yield self.price_map[keys[index]]
            except IndexError:
                yield None

    def run(self):
        for symbol in self.get_symbols():
            if symbol:
                canvas = self.get_ticker_canvas(symbol)
            else:
                canvas = self.get_error_canvas()
            self.matrix.SwapOnVSync(canvas)
            time.sleep(self.sleep)


if __name__ == '__main__':
    BinanceTicker().process()

        

        

    



    
