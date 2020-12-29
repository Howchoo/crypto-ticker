import json
import logging
import os
import requests
import sys


# Set up the logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


API_CLASS_MAP = {'coinmarketcap': 'CoinMarketCap', 'coingecko': 'CoinGecko'}


def get_api_cls(api_name):
    """

    Args:
        api_name (str): The name of the API to use.
    """
    if api_name not in API_CLASS_MAP:
        raise RuntimeError(f'"{api_name}" api is not implemented.')
    return getattr(sys.modules[__name__], API_CLASS_MAP[api_name])


class PriceAPI:
    """The base class for Price API"""

    def __init__(self, symbols):
        self.symbols = symbols

    def fetch_price_data(self):
        """Fetch new price data from the API.

        Returns:
            A list of dicts that represent price data for a single asset. For example:

            [{'symbol': .., 'price': .., 'change_24h': ..}]
        """
        raise NotImplementedError


class CoinMarketCap(PriceAPI):
    SANDBOX_API = 'https://sandbox-api.coinmarketcap.com'
    PRODUCTION_API = 'https://pro-api.coinmarketcap.com'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Confirm an API key is present
        try:
            self.api_key = os.environ['CMC_API_KEY']
        except KeyError:
            raise RuntimeError('CMC_API_KEY environment variable must be set.')

        self.env = (
            self.SANDBOX_API
            if os.environ.get('SANDBOX', '') == 'true'
            else self.PRODUCTION_API
        )

    def fetch_price_data(self):
        """Fetch new price data from the CoinMarketCap API"""
        logger.info('`fetch_price_data` called.')

        response = requests.get(
            '{0}/v1/cryptocurrency/quotes/latest'.format(self.api),
            params={'symbol': self.symbols},
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
                change_24h = f"{data['quote']['USD']['percent_change_24h']:.1f}%"
            except KeyError:
                # TODO: Add error logging
                continue
            price_data.append(dict(symbol=symbol, price=price, change_24h=change_24h))

        return price_data


class CoinGecko(PriceAPI):
    API = 'https://api.coingecko.com/api/v3'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fetch the coin list and cache data for our symbols
        response = requests.get(f'{self.API}/coins/list')

        # The CoinGecko API uses ids to fetch price data
        symbol_map = {}

        for coin in response.json():
            symbol = coin['symbol']
            if symbol in self.symbols.split(','):
                symbol_map[coin['id']] = symbol

        self.symbol_map = symbol_map

    def fetch_price_data(self):
        """Fetch new price data from the CoinGecko API"""
        logger.info('`fetch_price_data` called.')
        logger.info(f'Fetching data for {self.symbol_map}.')

        # Make the API request
        response = requests.get(
            f'{self.API}/simple/price',
            params={
                'ids': ','.join(list(self.symbol_map.keys())),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
            },
        )
        price_data = []

        logger.info(response.json())

        for coin_id, data in response.json().items():
            try:
                price = f"${data['usd']:,.2f}"
                change_24h = f"{data['usd_24h_change']:.1f}%"
            except KeyError:
                continue

            price_data.append(
                dict(
                    symbol=self.symbol_map[coin_id], price=price, change_24h=change_24h
                )
            )

        return price_data
