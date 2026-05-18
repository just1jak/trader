from flask_restx import Namespace, Resource, fields
from ..utils.tradovate import TradovateClient
from ..utils.backtest import run_backtest
import pandas as pd
import json

api = Namespace('backtest', description='Backtesting operations')

# Define the expected input model for backtest request
backtest_input = api.model('BacktestInput', {
    'symbol': fields.String(required=True, description='Futures symbol, e.g., ES'),
    'from': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'to': fields.String(required=True, description='End date (YYYY-MM-DD)'),
    'timeframe': fields.String(required=True, description='Candle size, e.g., 1min, 5min, 1h'),
    'strategy': fields.String(required=True, description='Strategy name to use'),
    'params': fields.Raw(required=True, description='Strategy parameters as JSON object')
})

@api.route('')
class BacktestResource(Resource):
    @api.expect(backtest_input)
    @api.response(200, 'Success')
    @api.response(400, 'Validation Error')
    @api.response(500, 'Internal Server Error')
    def post(self):
        """
        Run a backtest with the given parameters.
        """
        payload = api.payload
        try:
            # Fetch historical data from Tradovate
            client = TradovateClient()
            # Convert timeframe to Tradovate interval format (e.g., 1min -> 1, 5min ->5, 1h ->60)
            interval_map = {'1min': 1, '5min': 5, '15min': 15, '1h': 60, '1d': 'D'}
            interval = interval_map.get(payload['timeframe'])
            if interval is None:
                return {'error': f'Unsupported timeframe: {payload["timeframe"]}'}, 400

            # Tradovate expects timestamps in milliseconds
            from_ts = int(pd.Timestamp(payload['from']).timestamp() * 1000)
            to_ts = int(pd.Timestamp(payload['to']).timestamp() * 1000)

            candles = client.get_historic(
                symbol=payload['symbol'],
                interval=interval,
                from_timestamp=from_ts,
                to_timestamp=to_ts
            )
            if candles.empty:
                return {'error': 'No data returned from Tradovate for the given period'}, 404

            # Run backtest
            results = run_backtest(
                data=candles,
                strategy_name=payload['strategy'],
                params=payload['params']
            )
            return results, 200
        except Exception as e:
            return {'error': str(e)}, 500