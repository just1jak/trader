from flask import current_app, request
from flask_restx import Namespace, Resource, fields
import math
import pandas as pd

from utils.backtest import run_backtest
from utils.backtest_data import candles_to_records, load_sample_candles
from utils.congressional import list_congressional_trades, run_congressional_backtest
from utils.etrade import ETradeClient, ETradeConfigError
from utils.etrade_collection import (
    clear_pending_oauth,
    create_paper_session,
    extract_quote_price,
    get_paper_session,
    list_paper_marks,
    list_paper_sessions,
    list_market_snapshots,
    load_pending_oauth,
    mark_paper_session,
    save_market_snapshot,
    save_pending_oauth,
)
from utils.options_backtest import run_long_option_backtest
from utils.provider_config import apply_to_flask_config, provider_status, save_provider_settings
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
    'strategy': fields.String(required=False, description='long_call, long_put, bull_call_spread, bear_put_spread, or long_straddle'),
    'short_strike': fields.Float(required=False, description='Short leg strike for spread strategies'),
    'short_premium': fields.Float(required=False, description='Premium received for spread short leg', default=0),
})

provider_settings_input = api.model('ProviderSettingsInput', {
    'values': fields.Raw(required=True, description='Provider environment key/value settings'),
})

etrade_oauth_complete_input = api.model('ETradeOAuthCompleteInput', {
    'verifier': fields.String(required=True, description='Verification code from E*TRADE authorization page'),
})

etrade_collect_input = api.model('ETradeCollectInput', {
    'symbols': fields.String(required=True, description='Comma-separated symbols to quote'),
    'detailFlag': fields.String(required=False, description='E*TRADE quote detail flag', default='ALL'),
})

paper_session_input = api.model('PaperSessionInput', {
    'name': fields.String(required=False, description='Session name'),
    'symbol': fields.String(required=True, description='Symbol to forward test, e.g., AAPL'),
    'strategy': fields.String(required=False, description='forward_long, forward_short, or observe_only', default='forward_long'),
    'quantity': fields.Float(required=False, description='Simulated unit count', default=1),
    'initial_cash': fields.Float(required=False, description='Starting notional cash balance', default=100000),
    'notes': fields.String(required=False, description='Research notes for this paper session'),
})

paper_mark_input = api.model('PaperMarkInput', {
    'session_id': fields.Integer(required=True, description='Paper session id'),
    'price': fields.Float(required=False, description='Manual mark price; omit to use live E*TRADE quote'),
    'detailFlag': fields.String(required=False, description='E*TRADE quote detail flag', default='ALL'),
})

congress_backtest_input = api.model('CongressBacktestInput', {
    'holding_days': fields.Integer(required=False, description='Holding window after disclosed trade', default=5),
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
                'tradovate': _provider_configured('tradovate'),
                'etrade_market_data': _provider_configured('etrade'),
            },
            'routes': {
                'backtest': '/api/v1/backtest',
                'backtest_data': '/api/v1/market/backtest-data',
                'etrade_oauth_start': '/api/v1/etrade/oauth/start',
                'etrade_live_quote': '/api/v1/etrade/live/quote',
                'etrade_collect_quote': '/api/v1/etrade/live/collect',
                'etrade_snapshots': '/api/v1/etrade/live/snapshots',
                'paper_sessions': '/api/v1/paper/sessions',
                'paper_mark': '/api/v1/paper/mark',
                'quote': '/api/v1/market/quote/{symbols}',
                'option_expirations': '/api/v1/market/options/expirations/{symbol}',
                'option_chain': '/api/v1/market/options/chain/{symbol}',
                'options_backtest': '/api/v1/options/backtest',
                'congress_trades': '/api/v1/congress/trades',
                'congress_backtest': '/api/v1/congress/backtest',
            },
        }, 200


@api.route('/settings/providers')
class ProviderSettingsCollectionResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {'providers': provider_status()}, 200


@api.route('/settings/providers/<string:provider_key>')
class ProviderSettingsResource(Resource):
    @api.expect(provider_settings_input)
    @api.response(200, 'Saved')
    @api.response(400, 'Validation Error')
    def post(self, provider_key):
        try:
            providers = save_provider_settings(provider_key, (api.payload or {}).get('values') or {})
            apply_to_flask_config(current_app)
            return {'providers': providers}, 200
        except ValueError as exc:
            return {'error': str(exc)}, 400


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


@api.route('/etrade/oauth/start')
class ETradeOAuthStartResource(Resource):
    @api.response(200, 'Request token created')
    @api.response(400, 'Configuration or validation error')
    def post(self):
        try:
            client = ETradeClient()
            request_token = client.request_token()
            pending = save_pending_oauth(request_token)
            return {
                'authorize_url': client.authorize_url(request_token['oauth_token']),
                'request_token': pending,
                'message': 'Open the authorization URL, approve access, then paste the verifier code here.',
            }, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/etrade/oauth/complete')
class ETradeOAuthCompleteResource(Resource):
    @api.expect(etrade_oauth_complete_input)
    @api.response(200, 'Access token saved')
    @api.response(400, 'Configuration or validation error')
    def post(self):
        payload = api.payload or {}
        try:
            pending = load_pending_oauth()
            token_payload = ETradeClient().exchange_access_token(
                request_token=pending.get('oauth_token'),
                request_token_secret=pending.get('oauth_token_secret'),
                verifier=payload.get('verifier'),
            )
            providers = save_provider_settings('etrade', {
                'ETRADE_ACCESS_TOKEN': token_payload['oauth_token'],
                'ETRADE_ACCESS_TOKEN_SECRET': token_payload['oauth_token_secret'],
            })
            clear_pending_oauth()
            apply_to_flask_config(current_app)
            return {'providers': providers, 'message': 'E*TRADE access token saved. Tokens expire daily.'}, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/etrade/oauth/renew')
class ETradeOAuthRenewResource(Resource):
    @api.response(200, 'Access token renewed')
    @api.response(400, 'Configuration or validation error')
    def post(self):
        try:
            return {'message': ETradeClient().renew_access_token()}, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/etrade/live/quote')
class ETradeLiveQuoteResource(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Configuration or validation error')
    def get(self):
        symbols = request.args.get('symbols', 'AAPL')
        detail_flag = request.args.get('detailFlag', 'ALL')
        try:
            return {
                'symbols': symbols,
                'detailFlag': detail_flag,
                'data': ETradeClient().get_quote(symbols, detail_flag=detail_flag),
            }, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/etrade/live/collect')
class ETradeCollectQuoteResource(Resource):
    @api.expect(etrade_collect_input)
    @api.response(200, 'Snapshot saved')
    @api.response(400, 'Configuration or validation error')
    def post(self):
        payload = api.payload or {}
        symbols = payload.get('symbols') or 'AAPL'
        detail_flag = payload.get('detailFlag') or 'ALL'
        try:
            data = ETradeClient().get_quote(symbols, detail_flag=detail_flag)
            snapshot = save_market_snapshot(
                snapshot_type='quote',
                symbol=symbols,
                request_params={'symbols': symbols, 'detailFlag': detail_flag},
                response_payload=data,
            )
            return {'snapshot': snapshot, 'data': data, 'snapshots': list_market_snapshots()}, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/etrade/live/snapshots')
class ETradeSnapshotCollectionResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {'snapshots': list_market_snapshots(request.args.get('limit', 25))}, 200


@api.route('/paper/sessions')
class PaperSessionCollectionResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {'sessions': list_paper_sessions(request.args.get('limit', 50))}, 200

    @api.expect(paper_session_input)
    @api.response(201, 'Paper session created')
    @api.response(400, 'Validation error')
    def post(self):
        payload = api.payload or {}
        try:
            session = create_paper_session(
                name=payload.get('name'),
                symbol=payload.get('symbol'),
                strategy=payload.get('strategy') or 'forward_long',
                quantity=payload.get('quantity') or 1,
                initial_cash=payload.get('initial_cash') or 100000,
                notes=payload.get('notes') or '',
            )
            return {'session': session, 'sessions': list_paper_sessions()}, 201
        except ValueError as exc:
            return {'error': str(exc)}, 400


@api.route('/paper/sessions/<int:session_id>/marks')
class PaperSessionMarksResource(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Validation error')
    def get(self, session_id):
        try:
            get_paper_session(session_id)
            return {'marks': list_paper_marks(session_id, request.args.get('limit', 100))}, 200
        except ValueError as exc:
            return {'error': str(exc)}, 400


@api.route('/paper/mark')
class PaperMarkResource(Resource):
    @api.expect(paper_mark_input)
    @api.response(200, 'Paper session marked')
    @api.response(400, 'Configuration or validation error')
    def post(self):
        payload = api.payload or {}
        try:
            session = get_paper_session(payload.get('session_id'))
            price_source = 'manual'
            snapshot = None

            if payload.get('price') in (None, ''):
                detail_flag = payload.get('detailFlag') or 'ALL'
                quote_payload = ETradeClient().get_quote(session['symbol'], detail_flag=detail_flag)
                price_info = extract_quote_price(quote_payload)
                price = price_info['price']
                price_source = f"etrade:{price_info['field']}"
                snapshot = save_market_snapshot(
                    snapshot_type='paper_quote',
                    symbol=session['symbol'],
                    request_params={
                        'symbols': session['symbol'],
                        'detailFlag': detail_flag,
                        'paper_session_id': session['id'],
                    },
                    response_payload=quote_payload,
                )
                raw_payload = quote_payload
            else:
                price = payload.get('price')
                raw_payload = {'manual_price': price}

            mark = mark_paper_session(
                session_id=session['id'],
                price=price,
                raw_payload=raw_payload,
                source_snapshot_id=snapshot['id'] if snapshot else None,
            )
            mark['price_source'] = price_source
            return {
                'mark': mark,
                'marks': list_paper_marks(session['id']),
                'sessions': list_paper_sessions(),
            }, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except ValueError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


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
                strategy=payload.get('strategy'),
                short_strike=float(payload['short_strike']) if payload.get('short_strike') not in (None, '') else None,
                short_premium=float(payload.get('short_premium') or 0),
            )
            results['data_source'] = payload.get('source', 'sample')
            return _json_ready(results), 200
        except ValueError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 500


@api.route('/congress/trades')
class CongressTradesResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return list_congressional_trades(limit=request.args.get('limit', 50)), 200


@api.route('/congress/backtest')
class CongressBacktestResource(Resource):
    @api.expect(congress_backtest_input)
    @api.response(200, 'Success')
    def post(self):
        payload = api.payload or {}
        return _json_ready(run_congressional_backtest(payload.get('holding_days', 5))), 200


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


def _provider_configured(provider_key):
    providers = {provider['key']: provider for provider in provider_status()}
    return bool(providers.get(provider_key, {}).get('configured'))


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
