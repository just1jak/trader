from flask import current_app, request
from flask_restx import Namespace, Resource, fields
import math
import pandas as pd

from utils.backtest import run_backtest
from utils.backtest_data import candles_to_records, load_sample_candles
from utils.etrade import ETradeClient, ETradeConfigError
from utils.options_backtest import run_long_option_backtest
from utils.tradovate import TradovateClient


api = Namespace('trading', description='Backtesting and market-data operations')

STRATEGIES = {
    'ma_crossover': 'MA Crossover',
    'orb': 'Opening Range Breakout',
    'delta_scalp': 'Delta Scalp',
    'ema_scalp': 'Micro-Trend EMA Scalp',
    'support_resistance_flip': 'Support/Resistance Flip',
    'volume_profile_orderflow': 'Volume Profile Order Flow',
}

backtest_input = api.model('BacktestInput', {
    'symbol': fields.String(required=True, description='Futures symbol, e.g., ES'),
    'from': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'to': fields.String(required=True, description='End date (YYYY-MM-DD)'),
    'timeframe': fields.String(required=True, description='Candle size, e.g., 1min, 5min, 1h'),
    'strategy': fields.String(required=True, description='Strategy module name'),
    'params': fields.Raw(required=True, description='Strategy parameters as JSON object'),
    'source': fields.String(required=False, description='sample or tradovate', default='sample'),
})

options_backtest_input = api.model('OptionsBacktestInput', {
    'symbol': fields.String(required=True, description='Underlying symbol, e.g., ES or AAPL'),
    'from': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'to': fields.String(required=True, description='End date (YYYY-MM-DD)'),
    'timeframe': fields.String(required=False, description='Candle size', default='1min'),
    'source': fields.String(required=False, description='sample', default='sample'),
    'option_type': fields.String(required=True, description='CALL or PUT'),
    'strike': fields.Float(required=True, description='Option strike'),
    'premium': fields.Float(required=True, description='Entry premium per contract'),
    'contracts': fields.Integer(required=False, description='Number of contracts', default=1),
    'multiplier': fields.Integer(required=False, description='Contract multiplier', default=100),
})


@api.route('/health')
class HealthResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {
            'status': 'ok',
            'mode': 'simulation',
            'live_trading_enabled': False,
            'sources': {
                'sample': True,
                'tradovate': bool(current_app.config.get('TRADOVATE_API_KEY')),
                'etrade_market_data': bool(current_app.config.get('ETRADE_CONSUMER_KEY')),
            },
            'routes': {
                'backtest': '/api/v1/backtest',
                'backtest_data': '/api/v1/market/backtest-data',
                'quote': '/api/v1/market/quote/{symbols}',
                'option_expirations': '/api/v1/market/options/expirations/{symbol}',
                'option_chain': '/api/v1/market/options/chain/{symbol}',
                'options_backtest': '/api/v1/options/backtest',
            },
        }, 200


@api.route('/strategies')
class StrategiesResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {
            'strategies': [
                {'key': key, 'label': label}
                for key, label in STRATEGIES.items()
            ]
        }, 200


@api.route('/backtest')
class BacktestResource(Resource):
    @api.expect(backtest_input)
    @api.response(200, 'Success')
    @api.response(400, 'Validation Error')
    @api.response(500, 'Internal Server Error')
    def post(self):
        payload = api.payload or {}
        try:
            candles = _load_backtest_candles(payload)
            if candles.empty:
                return {'error': 'No data available for the requested period'}, 404

            results = run_backtest(
                data=candles,
                strategy_name=payload['strategy'],
                params=payload.get('params') or {},
            )
            results['data_source'] = payload.get('source', 'sample')
            return _json_ready(results), 200
        except ValueError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 500


@api.route('/market/backtest-data')
class BacktestDataResource(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Validation Error')
    def get(self):
        source = request.args.get('source', 'sample')
        symbol = request.args.get('symbol', 'ES')
        timeframe = request.args.get('timeframe', '1min')
        start = request.args.get('from')
        end = request.args.get('to')

        if source == 'etrade':
            return {
                'error': 'E*TRADE market APIs provide quote and option-chain snapshots here, not historical OHLCV candles.',
                'available_sources': ['sample', 'tradovate'],
            }, 400

        try:
            candles = _load_backtest_candles({
                'source': source,
                'symbol': symbol,
                'timeframe': timeframe,
                'from': start,
                'to': end,
            })
            return {
                'source': source,
                'symbol': symbol,
                'timeframe': timeframe,
                'rows': len(candles),
                'candles': candles_to_records(candles),
            }, 200
        except ValueError as exc:
            return {'error': str(exc)}, 400


@api.route('/market/quote/<string:symbols>')
class ETradeQuoteResource(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Configuration or validation error')
    def get(self, symbols):
        detail_flag = request.args.get('detailFlag', 'ALL')
        try:
            return ETradeClient().get_quote(symbols, detail_flag=detail_flag), 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/market/options/expirations/<string:symbol>')
class ETradeOptionExpirationsResource(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Configuration or validation error')
    def get(self, symbol):
        try:
            return ETradeClient().get_option_expirations(
                symbol=symbol,
                expiry_type=request.args.get('expiryType'),
            ), 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/market/options/chain/<string:symbol>')
class ETradeOptionChainResource(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Configuration or validation error')
    def get(self, symbol):
        args = request.args
        try:
            return ETradeClient().get_option_chain(
                symbol=symbol,
                expiry_year=args.get('expiryYear'),
                expiry_month=args.get('expiryMonth'),
                expiry_day=args.get('expiryDay'),
                strike_price_near=args.get('strikePriceNear'),
                no_of_strikes=args.get('noOfStrikes'),
                chain_type=args.get('chainType', 'CALLPUT'),
                include_weekly=_to_bool(args.get('includeWeekly'), default=False),
                skip_adjusted=_to_bool(args.get('skipAdjusted'), default=True),
                option_category=args.get('optionCategory', 'STANDARD'),
                price_type=args.get('priceType', 'ATNM'),
            ), 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/options/backtest')
class OptionsBacktestResource(Resource):
    @api.expect(options_backtest_input)
    @api.response(200, 'Success')
    @api.response(400, 'Validation Error')
    def post(self):
        payload = api.payload or {}
        try:
            candles = _load_backtest_candles(payload)
            results = run_long_option_backtest(
                data=candles,
                option_type=payload['option_type'],
                strike=float(payload['strike']),
                premium=float(payload['premium']),
                contracts=int(payload.get('contracts') or 1),
                multiplier=int(payload.get('multiplier') or 100),
            )
            results['data_source'] = payload.get('source', 'sample')
            return _json_ready(results), 200
        except ValueError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 500


def _load_backtest_candles(payload):
    source = payload.get('source', 'sample')
    if source == 'sample':
        return load_sample_candles(
            symbol=payload.get('symbol', 'ES'),
            timeframe=payload.get('timeframe', '1min'),
            start=payload.get('from'),
            end=payload.get('to'),
        )
    if source == 'tradovate':
        return _load_tradovate_candles(payload)
    raise ValueError(f'Unsupported backtest data source: {source}')


def _load_tradovate_candles(payload):
    interval_map = {'1min': 1, '5min': 5, '15min': 15, '1h': 60, '1d': 'D'}
    interval = interval_map.get(payload.get('timeframe'))
    if interval is None:
        raise ValueError(f'Unsupported timeframe: {payload.get("timeframe")}')

    from_ts = int(pd.Timestamp(payload['from']).timestamp() * 1000)
    to_ts = int(pd.Timestamp(payload['to']).timestamp() * 1000)
    return TradovateClient().get_historic(
        symbol=payload['symbol'],
        interval=interval,
        from_timestamp=from_ts,
        to_timestamp=to_ts,
    )


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in {'1', 'true', 'yes', 'y'}


def _json_ready(value):
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, 'item'):
        return _json_ready(value.item())
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
