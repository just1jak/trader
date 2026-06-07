import base64
import hashlib
import hmac
import time
import uuid
from urllib.parse import quote, urlencode

import requests

from config import Config


class ETradeConfigError(RuntimeError):
    pass


class ETradeClient:
    """
    Read-only E*TRADE market API client.

    The E*TRADE API uses OAuth 1.0a with HMAC-SHA1 signatures. This client
    expects an already-authorized access token and token secret in env vars.
    It does not implement order placement.
    """

    def __init__(self):
        self.base_url = Config.ETRADE_BASE_URL.rstrip('/')
        self.consumer_key = Config.ETRADE_CONSUMER_KEY
        self.consumer_secret = Config.ETRADE_CONSUMER_SECRET
        self.access_token = Config.ETRADE_ACCESS_TOKEN
        self.access_token_secret = Config.ETRADE_ACCESS_TOKEN_SECRET
        self.session = requests.Session()

    @property
    def is_configured(self):
        return all([
            self.consumer_key,
            self.consumer_secret,
            self.access_token,
            self.access_token_secret,
        ])

    def require_configured(self):
        if not self.is_configured:
            raise ETradeConfigError(
                'E*TRADE credentials are not configured. Set ETRADE_CONSUMER_KEY, '
                'ETRADE_CONSUMER_SECRET, ETRADE_ACCESS_TOKEN, and ETRADE_ACCESS_TOKEN_SECRET.'
            )

    def get_quote(self, symbols, detail_flag='ALL'):
        path = f'/v1/market/quote/{symbols}.json'
        params = {'detailFlag': detail_flag}
        return self._get(path, params)

    def get_option_expirations(self, symbol, expiry_type=None):
        params = {'symbol': symbol}
        if expiry_type:
            params['expiryType'] = expiry_type
        return self._get('/v1/market/optionexpiredate.json', params)

    def get_option_chain(
        self,
        symbol,
        expiry_year=None,
        expiry_month=None,
        expiry_day=None,
        strike_price_near=None,
        no_of_strikes=None,
        chain_type='CALLPUT',
        include_weekly=False,
        skip_adjusted=True,
        option_category='STANDARD',
        price_type='ATNM',
    ):
        params = {
            'symbol': symbol,
            'chainType': chain_type,
            'includeWeekly': str(include_weekly).lower(),
            'skipAdjusted': str(skip_adjusted).lower(),
            'optionCategory': option_category,
            'priceType': price_type,
        }
        optional = {
            'expiryYear': expiry_year,
            'expiryMonth': expiry_month,
            'expiryDay': expiry_day,
            'strikePriceNear': strike_price_near,
            'noOfStrikes': no_of_strikes,
        }
        params.update({key: value for key, value in optional.items() if value not in (None, '')})
        return self._get('/v1/market/optionchains.json', params)

    def _get(self, path, params=None):
        self.require_configured()
        params = params or {}
        url = f'{self.base_url}{path}'
        headers = {
            'Accept': 'application/json',
            'Authorization': self._authorization_header('GET', url, params),
        }
        response = self.session.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def _authorization_header(self, method, url, params):
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': uuid.uuid4().hex,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': self.access_token,
            'oauth_version': '1.0',
        }
        signature_params = {**params, **oauth_params}
        oauth_params['oauth_signature'] = self._signature(method, url, signature_params)
        return 'OAuth ' + ', '.join(
            f'{quote(key)}="{quote(str(value), safe="")}"'
            for key, value in sorted(oauth_params.items())
        )

    def _signature(self, method, url, params):
        encoded_params = urlencode(
            sorted((str(key), str(value)) for key, value in params.items()),
            quote_via=quote,
            safe='',
        )
        base_string = '&'.join([
            method.upper(),
            quote(url, safe=''),
            quote(encoded_params, safe=''),
        ])
        signing_key = '&'.join([
            quote(self.consumer_secret or '', safe=''),
            quote(self.access_token_secret or '', safe=''),
        ])
        digest = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        return base64.b64encode(digest).decode()
