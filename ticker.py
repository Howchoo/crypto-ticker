#!/usr/bin/env python3

import itertools
import json
import logging
import os
import requests
import sys
import time

from frame import Frame
from rgbmatrix import graphics


SANDBOX_API = 'https://sandbox-api.coinmarketcap.com'
PRODUCTION_API = 'https://pro-api.coinmarketcap.com'


# Set up the logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Ticker(Frame):
    def __init__(self, *args, **kwargs):
        """Initialize the Ticker class

        Gather the users settings from environment variables, then initialize the
        LED Panel Frame class.
        """
        # initialize variables used for price data cache
        self._cached_price_data = None
        self._last_fetch_time = 0

        # Confirm an API key is present
        try:
            self.api_key = os.environ['CMC_API_KEY']
        except KeyError:
            raise RuntimeError('CMC_API_KEY environment variable must be set.')

        # Get user settings
        self.refresh_rate = int(os.environ.get('REFRESH_RATE', 300))  # 300s or 5m
        self.sleep = int(os.environ.get('SLEEP', 3))  # 3s
        self.api = (
            SANDBOX_API if os.environ.get('SANDBOX', '') == 'true' else PRODUCTION_API
        )

        super().__init__(*args, **kwargs)

    def get_symbols(self):
        """Get the symbols to include"""
        symbols = os.environ.get('SYMBOLS')
        if not symbols:
            return 'BTC,ETH'
        return symbols

    def fetch_price_data(self):
        """Fetch new price data from the API.

        Returns:
            A list of dicts that represent price data for a single asset. For example:

            [{'symbol': .., 'price': .., 'change_1h': ..}]
        """
        logger.info('`fetch_price_data` called.')

        response = requests.get(
            '{0}/v1/cryptocurrency/quotes/latest'.format(self.api),
            params={'symbol': self.get_symbols()},
            headers={'X-CMC_PRO_API_KEY': self.api_key},
        )
        price_data = []

        try:
            items = response.json().get('data', {}).items()
        except json.JSONDecodeError:
            logger.error(f'JSON decode error: {response.text}')
            return

        for symbol, data in items:
            try:
                price = f"${data['quote']['USD']['price']:,.2f}"
                change_1h = f"{data['quote']['USD']['percent_change_1h']:.1f}%"
                # Add + for positive changes
                if change_1h.startswith('-'):
                    change_1h = change_1h[1:]
            except KeyError:
                # TODO: Add error logging
                continue
            price_data.append(dict(symbol=symbol, price=price, change_1h=change_1h))
        return price_data

    @property
    def price_data(self):
        """Price data for the requested assets, update automatically.

        This function will return a cached copy of the asset prices unless its time to
        fetch fresh data. We'll use the REFRESH_RATE environment variable to determine
        if it's time to refresh data.

        Returns:
            Updated price data. See self.fetch_price_data.
        """
        # Determine if the cache is stale
        cache_is_stale = (time.time() - self._last_fetch_time) > self.refresh_rate

        # See if we should return the cached price data
        if self._cached_price_data and not cache_is_stale:
            logger.info('Using cached price data.')
            return self._cached_price_data

        # Otherwise fetch new data and set the _last_fetch_time
        price_data = self.fetch_price_data()
        self._last_fetch_time = time.time()
        self._cached_price_data = price_data

        return price_data

    def get_ticker_canvas(self, asset):
        """Build the ticker canvas given an asset

        Returns:
            A canvas object with the symbol, change, and price drawn.
        """
        # Generate a fresh canvas
        canvas = self.matrix.CreateFrameCanvas()
        canvas.Clear()

        # Create fonts for displaying prices
        font_symbol = graphics.Font()
        font_symbol.LoadFont('fonts/7x13.bdf')

        font_price = graphics.Font()
        font_price.LoadFont('fonts/6x12.bdf')

        font_change = graphics.Font()
        font_change.LoadFont('fonts/6x10.bdf')

        # To right align, we have to calculate the width of the text
        change_width = sum(
            [font_change.CharacterWidth(ord(c)) for c in asset['change_1h']]
        )
        change_x = 62 - change_width

        # Get colors
        main_color = graphics.Color(255, 255, 0)
        change_color = (
            graphics.Color(194, 24, 7)
            if asset['change_1h'].startswith('-')
            else graphics.Color(46, 139, 87)
        )

        # Draw the elements on the canvas
        graphics.DrawText(canvas, font_symbol, 3, 12, main_color, asset['symbol'])
        graphics.DrawText(canvas, font_price, 3, 28, main_color, asset['price'])
        graphics.DrawText(
            canvas, font_change, change_x, 10, change_color, asset['change_1h']
        )

        return canvas

    def get_error_canvas(self):
        """Build an error canvas to show on errors"""
        canvas = self.matrix.CreateFrameCanvas()
        canvas.Clear()
        font = graphics.Font()
        font.LoadFont('../rpi-rgb-led-matrix/fonts/7x13.bdf')
        color = graphics.Color(194, 24, 7)
        graphics.DrawText(canvas, font, 15, 20, color, 'ERROR')
        return canvas

    def get_assets(self):
        """Generator method that yields assets infinitely.

        Since it uses `self.price_data` it will always return the latest prices,
        respecting the REFRESH_RATE.
        """
        # The size of the price_data list should not change, even when updated
        price_data_length = len(self.price_data)

        for index in itertools.cycle(range(price_data_length)):
            try:
                yield self.price_data[index]
            except IndexError:
                yield None

    def run(self):
        """Run the loop and display ticker prices.

        This is called by process.
        """
        for asset in self.get_assets():
            if asset:
                canvas = self.get_ticker_canvas(asset)
            else:
                canvas = self.get_error_canvas()
            self.matrix.SwapOnVSync(canvas)
            time.sleep(self.sleep)


if __name__ == '__main__':
    Ticker().process()
