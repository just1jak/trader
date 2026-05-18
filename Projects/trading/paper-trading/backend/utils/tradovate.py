import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class TradovateClient:
    def __init__(self):
        self.base_url = os.getenv('TRADOVATE_BASE_URL', 'https://demo.tradovateapi.com/v1')
        self.api_key = os.getenv('TRADOVATE_API_KEY')
        self.api_secret = os.getenv('TRADOVATE_API_SECRET')
        self.access_token = None
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Tradovate and store access token."""
        auth_url = f"{self.base_url}/auth/accesstokenrequest"
        payload = {
            "name": self.api_key,
            "password": self.api_secret,
            "appId": "papertradingwebapp",
            "version": "1.0.0",
            "deviceId": "papertrading-web",
            "deviceType": "Browser"
        }
        response = self.session.post(auth_url, json=payload)
        response.raise_for_status()
        data = response.json()
        self.access_token = data['accessToken']
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}'
        })

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

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
        # Tradovate returns a list of objects: {timestamp, open, high, low, close, volume}
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # Ensure numeric columns are float
        for col in ['open','high','low','close','volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df