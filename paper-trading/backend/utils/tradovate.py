import requests
import pandas as pd
import os
from dotenv import load_dotenv
from flask import current_app, has_app_context

from config import Config

load_dotenv()


class TradovateConfigError(RuntimeError):
    pass


class TradovateClient:
    def __init__(self):
        self.base_url = _setting('TRADOVATE_BASE_URL', Config.TRADOVATE_BASE_URL).rstrip('/')
        self.username = _first_setting('TRADOVATE_USERNAME', 'TRADOVATE_API_KEY')
        self.password = _first_setting('TRADOVATE_PASSWORD', 'TRADOVATE_API_SECRET')
        self.app_id = _setting('TRADOVATE_APP_ID', Config.TRADOVATE_APP_ID) or 'papertradingwebapp'
        self.app_version = _setting('TRADOVATE_APP_VERSION', Config.TRADOVATE_APP_VERSION) or '1.0.0'
        self.cid = _setting('TRADOVATE_CID', Config.TRADOVATE_CID)
        self.api_secret = _setting('TRADOVATE_SECRET', Config.TRADOVATE_SECRET)
        self.device_id = _setting('TRADOVATE_DEVICE_ID', Config.TRADOVATE_DEVICE_ID) or 'papertrading-web'
        self.access_token = None
        self.md_access_token = None
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Tradovate and store access token."""
        if not self.username or not self.password:
            raise TradovateConfigError(
                'Tradovate username and password are not configured. Save TRADOVATE_USERNAME and '
                'TRADOVATE_PASSWORD in Settings. Legacy TRADOVATE_API_KEY/API_SECRET are only used as fallbacks.'
            )

        auth_url = f"{self.base_url}/auth/accesstokenrequest"
        payload = {
            "name": self.username,
            "password": self.password,
            "appId": self.app_id,
            "appVersion": self.app_version,
            "deviceId": self.device_id,
        }
        if self.cid:
            payload['cid'] = self.cid
        if self.api_secret:
            payload['sec'] = self.api_secret
        try:
            response = self.session.post(
                auth_url,
                json=payload,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=20,
            )
            data = response.json()
        except requests.RequestException as exc:
            raise TradovateConfigError(f'Tradovate authentication request failed: {exc}') from exc
        except ValueError as exc:
            raise TradovateConfigError('Tradovate authentication returned a non-JSON response.') from exc

        if response.status_code >= 400:
            message = data.get('errorText') or data.get('error') or data.get('message') or response.reason
            raise TradovateConfigError(f'Tradovate authentication failed ({response.status_code}): {message}')
        self.access_token = data.get('accessToken')
        self.md_access_token = data.get('mdAccessToken') or self.access_token
        if not self.access_token:
            message = data.get('errorText') or data.get('error') or data.get('message') or 'No access token returned.'
            raise TradovateConfigError(f'Tradovate authentication failed: {message}')
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}'
        })

    def _get(self, endpoint, params=None, token=None):
        url = f"{self.base_url}{endpoint}"
        headers = {}
        if token or self.access_token:
            headers['Authorization'] = f'Bearer {token or self.access_token}'
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise TradovateConfigError(f'Tradovate request failed: {exc}') from exc
        except ValueError as exc:
            raise TradovateConfigError('Tradovate returned a non-JSON response.') from exc

    def get_historic(self, symbol, interval, from_timestamp, to_timestamp):
        """
        Fetch historical candles from Tradovate.
        interval: Tradovate interval (1,5,15,60,'D', etc.)
        from_timestamp/to_timestamp: milliseconds since epoch.
        Returns a pandas DataFrame with columns: ['timestamp','open','high','low','close','volume']
        """
        endpoint = f"/md/historic"
        params = {
            "symbol": symbol,
            "interval": interval,
            "from": from_timestamp,
            "to": to_timestamp
        }
        data = self._get(endpoint, params=params, token=self.md_access_token)
        if isinstance(data, dict) and 'errorText' in data:
            raise TradovateConfigError(f"Tradovate historic request failed: {data['errorText']}")
        if isinstance(data, dict) and 'candles' in data:
            data = data['candles']
        if not isinstance(data, list):
            raise TradovateConfigError('Tradovate historic response did not contain candle rows.')
        # Tradovate returns a list of objects: {timestamp, open, high, low, close, volume}
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        if 'timestamp' not in df.columns:
            raise TradovateConfigError('Tradovate candle rows did not include timestamps.')
        if 'volume' not in df.columns:
            up_volume = pd.to_numeric(df.get('upVolume', 0), errors='coerce').fillna(0)
            down_volume = pd.to_numeric(df.get('downVolume', 0), errors='coerce').fillna(0)
            df['volume'] = up_volume + down_volume
        if pd.api.types.is_numeric_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        # Ensure numeric columns are float
        for col in ['open','high','low','close','volume']:
            if col not in df.columns:
                raise TradovateConfigError(f'Tradovate candle rows did not include {col}.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df[['open', 'high', 'low', 'close', 'volume']].dropna()


def _setting(key, fallback=None):
    if has_app_context():
        return current_app.config.get(key, fallback)
    return os.getenv(key, fallback)


def _first_setting(*keys):
    for key in keys:
        value = _setting(key)
        if value:
            return value
    return None
