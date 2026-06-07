import base64
import hashlib
import hmac
import time
import uuid
from urllib.parse import parse_qsl, quote, urlencode

import requests
from flask import current_app, has_app_context

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
        self.base_url = _setting('ETRADE_BASE_URL', Config.ETRADE_BASE_URL).rstrip('/')
        self.etrade_env = str(_setting('ETRADE_ENV', Config.ETRADE_ENV) or 'sandbox').lower()
        self.consumer_key = _setting('ETRADE_CONSUMER_KEY', Config.ETRADE_CONSUMER_KEY)
        self.consumer_secret = _setting('ETRADE_CONSUMER_SECRET', Config.ETRADE_CONSUMER_SECRET)
        self.access_token = _setting('ETRADE_ACCESS_TOKEN', Config.ETRADE_ACCESS_TOKEN)
        self.access_token_secret = _setting('ETRADE_ACCESS_TOKEN_SECRET', Config.ETRADE_ACCESS_TOKEN_SECRET)
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

    def require_consumer_configured(self):
        if not self.consumer_key or not self.consumer_secret:
            raise ETradeConfigError('E*TRADE consumer key and consumer secret are required before OAuth connect.')

    def request_token(self):
        self.require_consumer_configured()
        url = f'{self.base_url}/oauth/request_token'
        oauth_params = self._base_oauth_params()
        oauth_params['oauth_callback'] = 'oob'
        headers = {
            'Accept': 'application/x-www-form-urlencoded',
            'Authorization': self._authorization_header('GET', url, {}, oauth_params=oauth_params, token_secret=''),
        }
        response = self.session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        payload = dict(parse_qsl(response.text))
        if not payload.get('oauth_token') or not payload.get('oauth_token_secret'):
            raise ETradeConfigError('E*TRADE did not return a request token.')
        return payload

    def authorize_url(self, request_token):
        self.require_consumer_configured()
        params = urlencode({'key': self.consumer_key, 'token': request_token}, quote_via=quote, safe='')
        return f'https://us.etrade.com/e/t/etws/authorize?{params}'

    def exchange_access_token(self, request_token, request_token_secret, verifier):
        self.require_consumer_configured()
        if not request_token or not request_token_secret:
            raise ETradeConfigError('Start OAuth first so the request token secret is available.')
        if not verifier:
            raise ETradeConfigError('Paste the E*TRADE verification code before completing OAuth.')

        url = f'{self.base_url}/oauth/access_token'
        oauth_params = self._base_oauth_params(oauth_token=request_token)
        oauth_params['oauth_verifier'] = verifier
        headers = {
            'Accept': 'application/x-www-form-urlencoded',
            'Authorization': self._authorization_header(
                'GET',
                url,
                {},
                oauth_params=oauth_params,
                token_secret=request_token_secret,
            ),
        }
        response = self.session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        payload = dict(parse_qsl(response.text))
        if not payload.get('oauth_token') or not payload.get('oauth_token_secret'):
            raise ETradeConfigError('E*TRADE did not return an access token.')
        return payload

    def renew_access_token(self):
        self.require_configured()
        url = f'{self.base_url}/oauth/renew_access_token'
        headers = {
            'Accept': 'text/plain',
            'Authorization': self._authorization_header('GET', url, {}),
        }
        response = self.session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text or 'Access token renewed'

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

    def _base_oauth_params(self, oauth_token=None):
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': uuid.uuid4().hex,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0',
        }
        token = self.access_token if oauth_token is None else oauth_token
        if token:
            oauth_params['oauth_token'] = token
        return oauth_params

    def _authorization_header(self, method, url, params, oauth_params=None, token_secret=None):
        oauth_params = oauth_params or self._base_oauth_params()
        signature_params = {**params, **oauth_params}
        secret = self.access_token_secret if token_secret is None else token_secret
        oauth_params['oauth_signature'] = self._signature(method, url, signature_params, token_secret=secret)
        return 'OAuth ' + ', '.join(
            f'{quote(key)}="{quote(str(value), safe="")}"'
            for key, value in sorted(oauth_params.items())
        )

    def _signature(self, method, url, params, token_secret=None):
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
            quote(token_secret or '', safe=''),
        ])
        digest = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        return base64.b64encode(digest).decode()


def _setting(key, fallback=None):
    if has_app_context():
        return current_app.config.get(key, fallback)
    return fallback
