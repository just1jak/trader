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
        self.api_key = _setting('TRADOVATE_API_KEY', Config.TRADOVATE_API_KEY)
        self.api_secret = _setting('TRADOVATE_API_SECRET', Config.TRADOVATE_API_SECRET)
        self.access_token = None
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Tradovate and store access token."""
        if not self.api_key or not self.api_secret:
            raise TradovateConfigError('Tradovate API key and secret are not configured.')

        auth_url = f"{self.base_url}/auth/accesstokenrequest"
        payload = {
            "name": self.api_key,
            "password": self.api_secret,
            "appId": "papertradingwebapp",
            "version": "1.0.0",
            "deviceId": "papertrading-web",
            "deviceType": "Browser"
        }
        try:
            response = self.session.post(auth_url, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise TradovateConfigError(f'Tradovate authentication request failed: {exc}') from exc
        except ValueError as exc:
            raise TradovateConfigError('Tradovate authentication returned a non-JSON response.') from exc

        self.access_token = data.get('accessToken')
        if not self.access_token:
            message = data.get('errorText') or data.get('error') or data.get('message') or 'No access token returned.'
            raise TradovateConfigError(f'Tradovate authentication failed: {message}')
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}'
        })

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=20)
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
        data = self._get(endpoint, params=params)
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
