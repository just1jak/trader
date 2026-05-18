import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    TRADOVATE_API_KEY = os.getenv('TRADOVATE_API_KEY')
    TRADOVATE_API_SECRET = os.getenv('TRADOVATE_API_SECRET')
    TRADOVATE_BASE_URL = os.getenv('TRADOVATE_BASE_URL', 'https://demo.tradovateapi.com/v1')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://papertrader:papertrader@db:5432/papertrading'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False