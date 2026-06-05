from flask import Flask
from flask_restx import Api
import os
from config import Config
from api.routes import api as api_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.after_request
    def add_cors_headers(response):
        response.headers.setdefault('Access-Control-Allow-Origin', app.config['CORS_ORIGINS'])
        response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response

    api = Api(app, version='1.0', title='Paper Trading API',
              description='API for backtesting and paper trading')
    api.add_namespace(api_blueprint, path='/api/v1')
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=True)
