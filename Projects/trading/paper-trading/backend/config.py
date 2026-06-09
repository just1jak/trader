import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    TRADOVATE_USERNAME = os.getenv('TRADOVATE_USERNAME')
    TRADOVATE_PASSWORD = os.getenv('TRADOVATE_PASSWORD')
    TRADOVATE_APP_ID = os.getenv('TRADOVATE_APP_ID', 'papertradingwebapp')
    TRADOVATE_APP_VERSION = os.getenv('TRADOVATE_APP_VERSION', '1.0.0')
    TRADOVATE_CID = os.getenv('TRADOVATE_CID')
    TRADOVATE_SECRET = os.getenv('TRADOVATE_SECRET')
    TRADOVATE_DEVICE_ID = os.getenv('TRADOVATE_DEVICE_ID', 'papertrading-web')
    TRADOVATE_API_KEY = os.getenv('TRADOVATE_API_KEY')
    TRADOVATE_API_SECRET = os.getenv('TRADOVATE_API_SECRET')
    TRADOVATE_BASE_URL = os.getenv('TRADOVATE_BASE_URL', 'https://demo.tradovateapi.com/v1')
    ETRADE_ENV = os.getenv('ETRADE_ENV', 'sandbox').lower()
    ETRADE_CONSUMER_KEY = os.getenv('ETRADE_CONSUMER_KEY')
    ETRADE_CONSUMER_SECRET = os.getenv('ETRADE_CONSUMER_SECRET')
    ETRADE_ACCESS_TOKEN = os.getenv('ETRADE_ACCESS_TOKEN')
    ETRADE_ACCESS_TOKEN_SECRET = os.getenv('ETRADE_ACCESS_TOKEN_SECRET')
    ETRADE_BASE_URL = os.getenv(
        'ETRADE_BASE_URL',
        'https://apisb.etrade.com' if ETRADE_ENV == 'sandbox' else 'https://api.etrade.com'
    )
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL', 'https://api.polygon.io')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://papertrader:papertrader@db:5432/papertrading'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
