import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
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
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://papertrader:papertrader@db:5432/papertrading'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
