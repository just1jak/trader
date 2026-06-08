from flask import current_app, request
from flask_restx import Namespace, Resource, fields
import math
import pandas as pd

from utils.backtest import run_backtest
from utils.backtest_data import candles_to_records, load_sample_candles
from utils.candle_cache import (
    cache_row_count,
    candle_cache_summary,
    load_cached_candles,
    save_cached_candles,
)
from utils.coinbase import CoinbaseClient, CoinbaseConfigError
from utils.congressional import list_congressional_trades, run_congressional_backtest
from utils.congressional_ingest_bridge import congressional_disclosure_counts, sync_congressional_disclosures
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
    summarize_quote_payload,
)
from utils.options_backtest import run_long_option_backtest
from utils.polygon import PolygonClient, PolygonConfigError
from utils.provider_config import apply_to_flask_config, clear_provider_settings, provider_status, save_provider_settings
from utils.tradovate import TradovateClient, TradovateConfigError
from utils.yahoo import YahooClient, YahooConfigError


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
    'source': fields.String(required=False, description='sample, coinbase, yahoo, tradovate, polygon, or cache', default='sample'),
})

options_backtest_input = api.model('OptionsBacktestInput', {
    'symbol': fields.String(required=True, description='Underlying symbol, e.g., ES or AAPL'),
    'from': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'to': fields.String(required=True, description='End date (YYYY-MM-DD)'),
    'timeframe': fields.String(required=False, description='Candle size', default='1min'),
    'source': fields.String(required=False, description='sample, coinbase, yahoo, tradovate, polygon, or cache', default='sample'),
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

provider_settings_clear_input = api.model('ProviderSettingsClearInput', {
    'keys': fields.List(fields.String, required=True, description='Provider environment keys to clear'),
})

etrade_oauth_complete_input = api.model('ETradeOAuthCompleteInput', {
    'verifier': fields.String(required=True, description='Verification code from E*TRADE authorization page'),
})

etrade_collect_input = api.model('ETradeCollectInput', {
    'symbols': fields.String(required=True, description='Comma-separated symbols to quote'),
    'detailFlag': fields.String(required=False, description='E*TRADE quote detail flag', default='ALL'),
})

candle_collect_input = api.model('CandleCollectInput', {
    'symbol': fields.String(required=True, description='Symbol to collect, e.g., ES or AAPL'),
    'from': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'to': fields.String(required=True, description='End date (YYYY-MM-DD)'),
    'timeframe': fields.String(required=True, description='Candle size, e.g., 1min, 5min, 1h, 1d'),
    'source': fields.String(required=True, description='Provider to collect from: sample, coinbase, yahoo, tradovate, or polygon'),
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

congress_ingest_input = api.model('CongressIngestInput', {
    'year': fields.Integer(required=False, description='Disclosure year to import'),
    'limit': fields.Integer(required=False, description='Maximum House PTR PDFs to download', default=25),
    'include_senate': fields.Boolean(required=False, description='Include Senate eFD-derived disclosure ingestion', default=True),
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
                'coinbase': True,
                'yahoo': True,
                'tradovate': _provider_configured('tradovate'),
                'etrade_market_data': _provider_configured('etrade'),
                'polygon': _provider_configured('polygon'),
                'cache': cache_row_count() > 0,
            },
            'routes': {
                'data_sources': '/api/v1/data/sources',
                'data_smoke_test': '/api/v1/data/smoke-test',
                'backtest': '/api/v1/backtest',
                'backtest_data': '/api/v1/market/backtest-data',
                'collect_candles': '/api/v1/market/candles/collect',
                'candle_cache': '/api/v1/market/candles/cache',
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
                'congress_ingest': '/api/v1/congress/ingest',
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


@api.route('/settings/providers/<string:provider_key>/clear')
class ProviderSettingsClearResource(Resource):
    @api.expect(provider_settings_clear_input)
    @api.response(200, 'Cleared')
    @api.response(400, 'Validation Error')
    def post(self, provider_key):
        try:
            providers = clear_provider_settings(provider_key, (api.payload or {}).get('keys') or [])
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
            data = ETradeClient().get_quote(symbols, detail_flag=detail_flag)
            return {
                'symbols': symbols,
                'detailFlag': detail_flag,
                'summary': summarize_quote_payload(data),
                'data': data,
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
            return {
                'snapshot': snapshot,
                'data': data,
                'summary': summarize_quote_payload(data),
                'snapshots': list_market_snapshots(),
            }, 200
        except ETradeConfigError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/etrade/live/snapshots')
class ETradeSnapshotCollectionResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {'snapshots': list_market_snapshots(request.args.get('limit', 25))}, 200


@api.route('/data/sources')
class DataSourcesResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {
            'probe': _to_bool(request.args.get('probe'), default=False),
            'sources': _data_source_status(_to_bool(request.args.get('probe'), default=False)),
        }, 200


@api.route('/data/smoke-test')
class DataSmokeTestResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        checks = _data_source_smoke_checks()
        return {
            'summary': _smoke_summary(checks),
            'checks': checks,
            'message': 'Read-only source verification completed. Blocked providers need credentials or fresh authorization before they can return live data.',
        }, 200


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
        except (CoinbaseConfigError, YahooConfigError, TradovateConfigError, PolygonConfigError) as exc:
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
                'available_sources': ['sample', 'coinbase', 'yahoo', 'tradovate', 'polygon', 'cache'],
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
        except (CoinbaseConfigError, YahooConfigError, TradovateConfigError, PolygonConfigError) as exc:
            return {'error': str(exc)}, 400


@api.route('/market/candles/cache')
class CandleCacheResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return {
            'rows': cache_row_count(),
            'datasets': candle_cache_summary(request.args.get('limit', 20)),
        }, 200


@api.route('/market/candles/collect')
class CandleCollectResource(Resource):
    @api.expect(candle_collect_input)
    @api.response(200, 'Candles collected')
    @api.response(400, 'Validation Error')
    def post(self):
        payload = api.payload or {}
        source = payload.get('source', 'sample')
        if source in {'cache', 'etrade'}:
            return {'error': f'Cannot collect candles from source={source}.'}, 400
        try:
            candles = _load_backtest_candles(payload)
            saved = save_cached_candles(
                source=source,
                symbol=payload.get('symbol'),
                timeframe=payload.get('timeframe'),
                candles=candles,
            )
            return {
                'saved': saved,
                'source': source,
                'symbol': payload.get('symbol'),
                'timeframe': payload.get('timeframe'),
                'rows': len(candles),
                'preview': _json_ready(_candle_preview(candles)),
                'cache': {
                    'rows': cache_row_count(),
                    'datasets': candle_cache_summary(),
                },
            }, 200
        except ValueError as exc:
            return {'error': str(exc)}, 400
        except (CoinbaseConfigError, YahooConfigError, TradovateConfigError, PolygonConfigError) as exc:
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
        except (CoinbaseConfigError, YahooConfigError, TradovateConfigError, PolygonConfigError) as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 500


@api.route('/congress/trades')
class CongressTradesResource(Resource):
    @api.response(200, 'Success')
    def get(self):
        return list_congressional_trades(limit=request.args.get('limit', 50)), 200


@api.route('/congress/ingest')
class CongressIngestResource(Resource):
    @api.expect(congress_ingest_input)
    @api.response(200, 'Disclosures synced')
    @api.response(400, 'Validation Error')
    @api.response(502, 'External source error')
    def post(self):
        payload = api.payload or {}
        try:
            summary = sync_congressional_disclosures(
                year=payload.get('year'),
                limit=payload.get('limit') or 25,
                include_senate=_to_bool(payload.get('include_senate'), default=True),
            )
            return {
                'summary': _json_ready(summary),
                'trades': list_congressional_trades(limit=25),
                'message': 'Congressional disclosure sync completed from House PTR PDFs and Senate eFD-derived data.',
            }, 200
        except ValueError as exc:
            return {'error': str(exc)}, 400
        except Exception as exc:
            return {'error': str(exc)}, 502


@api.route('/congress/backtest')
class CongressBacktestResource(Resource):
    @api.expect(congress_backtest_input)
    @api.response(200, 'Success')
    def post(self):
        payload = api.payload or {}
        return _json_ready(run_congressional_backtest(payload.get('holding_days', 5))), 200


def _data_source_status(probe=False):
    providers = {provider['key']: provider for provider in provider_status()}
    sources = []

    try:
        sample = load_sample_candles(symbol='ES', timeframe='1min', start='2025-01-02', end='2025-01-02')
        sources.append(_source_item(
            key='sample',
            label='Sample CSV',
            configured=True,
            status='ok' if not sample.empty else 'empty',
            rows=len(sample),
            detail='Local ES sample candles are available for credential-free backtests.',
            preview=_candle_preview(sample),
            next_steps=['Use this source for a quick smoke test before relying on external data.'],
        ))
    except Exception as exc:
        sources.append(_source_item('sample', 'Sample CSV', True, 'error', detail=_safe_error(exc)))

    try:
        coinbase = CoinbaseClient().get_candles(
            product_id='BTC-USD',
            timeframe='1d',
            start='2025-01-02',
            end='2025-01-10',
        )
        sources.append(_source_item(
            key='coinbase',
            label='Coinbase crypto candles',
            configured=True,
            status='ok' if not coinbase.empty else 'empty',
            rows=len(coinbase),
            detail='Public no-key crypto OHLCV candles are available for backtests and collection.',
            preview=_candle_preview(coinbase),
            next_steps=['Select Coinbase crypto in Backtest, then collect BTC-USD or ETH-USD candles into the local cache.'],
        ))
    except Exception as exc:
        sources.append(_source_item('coinbase', 'Coinbase crypto candles', True, 'error', detail=_safe_error(exc)))

    try:
        yahoo = YahooClient().get_chart(
            symbol='AAPL',
            timeframe='1d',
            start='2025-01-02',
            end='2025-01-31',
        )
        sources.append(_source_item(
            key='yahoo',
            label='Yahoo Finance stock candles',
            configured=True,
            status='ok' if not yahoo.empty else 'empty',
            rows=len(yahoo),
            detail='Public stock/ETF OHLCV candles are available for backtests and collection. This endpoint can rate-limit.',
            preview=_candle_preview(yahoo),
            next_steps=['Select Yahoo Finance in Backtest to collect stock or ETF candles without a Polygon key.'],
        ))
    except Exception as exc:
        sources.append(_source_item('yahoo', 'Yahoo Finance stock candles', True, 'error', detail=_safe_error(exc)))

    tradovate_configured = bool(providers.get('tradovate', {}).get('configured'))
    if not tradovate_configured:
        sources.append(_source_item(
            key='tradovate',
            label='Tradovate',
            configured=False,
            status='needs_config',
            detail='Save Tradovate credentials in Settings before probing futures candles.',
            next_steps=[
                'Open Settings and save TRADOVATE_USERNAME and TRADOVATE_PASSWORD.',
                'Use the demo base URL for demo accounts or the live base URL for live Tradovate accounts.',
                'Return here and run Probe sources to verify futures candle access.',
            ],
        ))
    elif probe:
        try:
            candles = _load_tradovate_candles({
                'symbol': 'ES',
                'timeframe': '1min',
                'from': '2025-01-02',
                'to': '2025-01-02',
            })
            sources.append(_source_item(
                key='tradovate',
                label='Tradovate',
                configured=True,
                status='ok' if not candles.empty else 'empty',
                rows=len(candles),
                detail='Tradovate historical futures probe completed.',
                preview=_candle_preview(candles),
            ))
        except Exception as exc:
            sources.append(_source_item(
                'tradovate',
                'Tradovate',
                True,
                'error',
                detail=_safe_error(exc),
                next_steps=[
                    'Confirm the Tradovate account type matches the configured base URL.',
                    'Re-save username/password and optional cid/sec fields in Settings.',
                    'Probe again after credentials are accepted.',
                ],
            ))
    else:
        sources.append(_source_item(
            key='tradovate',
            label='Tradovate',
            configured=True,
            status='ready',
            detail='Configured. Run a probe to verify live credential and market-data access.',
            next_steps=['Run Probe sources before using Tradovate for a backtest or candle collection.'],
        ))

    etrade_configured = bool(providers.get('etrade', {}).get('configured'))
    snapshot_count = len(list_market_snapshots(limit=100))
    if not etrade_configured:
        sources.append(_source_item(
            key='etrade_market_data',
            label='E*TRADE market data',
            configured=False,
            status='needs_config',
            rows=snapshot_count,
            detail='Complete E*TRADE OAuth before probing quotes and options chains.',
            next_steps=[
                'Open Settings and save E*TRADE consumer key and consumer secret.',
                'Open Live Data, click Connect E*TRADE, authorize access, and save the verifier code.',
            ],
        ))
    elif probe:
        try:
            quote = ETradeClient().get_quote('AAPL', detail_flag='ALL')
            summary = summarize_quote_payload(quote)
            sources.append(_source_item(
                key='etrade_market_data',
                label='E*TRADE market data',
                configured=True,
                status='ok' if summary else 'empty',
                rows=snapshot_count,
                detail='E*TRADE quote probe completed. Sandbox data may be historical/canned.',
                preview=summary[0] if summary else {},
            ))
        except Exception as exc:
            sources.append(_source_item(
                'etrade_market_data',
                'E*TRADE market data',
                True,
                'error',
                rows=snapshot_count,
                detail=_safe_error(exc),
                next_steps=[
                    'Open Live Data and click Connect E*TRADE to generate a fresh authorization URL.',
                    'Approve access, paste the verifier code, and save the new access token.',
                    'Confirm sandbox/live environment matches the token you authorized.',
                ],
            ))
    else:
        sources.append(_source_item(
            key='etrade_market_data',
            label='E*TRADE market data',
            configured=True,
            status='ready',
            rows=snapshot_count,
            detail='Configured. Run a probe to verify quote access; collected snapshots are counted here.',
            next_steps=['Run Probe sources or fetch a quote from Live Data before using E*TRADE paper marks.'],
        ))

    polygon_configured = bool(providers.get('polygon', {}).get('configured'))
    if not polygon_configured:
        sources.append(_source_item(
            key='polygon',
            label='Polygon',
            configured=False,
            status='needs_config',
            detail='Save a Polygon API key in Settings before probing stock aggregate bars.',
            next_steps=[
                'Open Settings and save POLYGON_API_KEY.',
                'Use Yahoo Finance for public stock candles while Polygon is unconfigured.',
                'Probe again after adding the key.',
            ],
        ))
    elif probe:
        try:
            candles = PolygonClient().get_aggregates('AAPL', timeframe='1d', start='2025-01-02', end='2025-01-10')
            sources.append(_source_item(
                key='polygon',
                label='Polygon',
                configured=True,
                status='ok' if not candles.empty else 'empty',
                rows=len(candles),
                detail='Polygon stock aggregate probe completed.',
                preview=_candle_preview(candles),
            ))
        except Exception as exc:
            sources.append(_source_item(
                'polygon',
                'Polygon',
                True,
                'error',
                detail=_safe_error(exc),
                next_steps=[
                    'Confirm the Polygon key is active and has aggregate-bar access.',
                    'Try a daily AAPL probe first, then widen symbols/timeframes after it passes.',
                ],
            ))
    else:
        sources.append(_source_item(
            key='polygon',
            label='Polygon',
            configured=True,
            status='ready',
            detail='Configured. Run a probe to verify aggregate-bar access.',
            next_steps=['Run Probe sources before collecting Polygon candles into the local cache.'],
        ))

    cache_rows = cache_row_count()
    cache_summary = candle_cache_summary(limit=1)
    sources.append(_source_item(
        key='cache',
        label='Cached candles',
        configured=True,
        status='ok' if cache_rows else 'empty',
        rows=cache_rows,
        detail='Local OHLCV candle cache populated by the collect-candles route.',
        preview=cache_summary[0] if cache_summary else {},
        next_steps=['Use source=cache to replay collected Yahoo, Coinbase, Polygon, Tradovate, or sample candles without another provider call.'],
    ))

    congressional = list_congressional_trades(limit=5)
    congressional_counts = congressional_disclosure_counts()
    total = congressional.get('total', 0)
    sources.append(_source_item(
        key='congress',
        label='Congressional disclosures',
        configured=True,
        status='ok' if total else 'empty',
        rows=total,
        detail=f"Local disclosure database row count: House {congressional_counts.get('house', 0)}, Senate {congressional_counts.get('senate', 0)}.",
        preview={
            'counts': congressional_counts,
            'latest': (congressional.get('trades') or [{}])[0],
        },
        next_steps=['Use the Congress tab to sync disclosures and run the congressional replay.'],
    ))

    return sources


def _data_source_smoke_checks():
    providers = {provider['key']: provider for provider in provider_status()}
    checks = []

    checks.append(_run_smoke_check(
        key='sample_backtest_data',
        label='Sample CSV candles',
        category='historical_candles',
        expected='Load local sample candles for a credential-free backtest.',
        action='Use Sample CSV for the fastest backend/UI smoke test.',
        fn=lambda: _smoke_candles(load_sample_candles(symbol='ES', timeframe='1min', start='2025-01-02', end='2025-01-02')),
    ))

    checks.append(_run_smoke_check(
        key='coinbase_backtest_data',
        label='Coinbase crypto candles',
        category='historical_candles',
        expected='Fetch public BTC-USD daily candles.',
        action='Collect BTC-USD or ETH-USD candles, then replay them from cache.',
        fn=lambda: _smoke_candles(CoinbaseClient().get_candles(
            product_id='BTC-USD',
            timeframe='1d',
            start='2025-01-02',
            end='2025-01-10',
        )),
    ))

    checks.append(_run_smoke_check(
        key='yahoo_backtest_data',
        label='Yahoo Finance stock candles',
        category='historical_candles',
        expected='Fetch public AAPL daily candles.',
        action='Use Yahoo for stock/ETF backtests while Polygon is unconfigured.',
        fn=lambda: _smoke_candles(YahooClient().get_chart(
            symbol='AAPL',
            timeframe='1d',
            start='2025-01-02',
            end='2025-01-31',
        )),
    ))

    cache_summary = candle_cache_summary(limit=1)
    if cache_summary:
        dataset = cache_summary[0]
        checks.append(_run_smoke_check(
            key='cache_replay',
            label='Cached candle replay',
            category='local_replay',
            expected='Replay the most recent cached OHLCV dataset.',
            action='Use Cached candles to run without another provider call.',
            fn=lambda dataset=dataset: _smoke_candles(load_cached_candles(
                symbol=dataset.get('symbol'),
                timeframe=dataset.get('timeframe'),
                start=dataset.get('first_timestamp'),
                end=dataset.get('last_timestamp'),
                source=dataset.get('source'),
            ), extra={'dataset': dataset}),
        ))
    else:
        checks.append(_smoke_item(
            key='cache_replay',
            label='Cached candle replay',
            category='local_replay',
            status='warning',
            rows=0,
            detail='No cached candle rows exist yet.',
            action='Collect sample, Coinbase, Yahoo, Tradovate, or Polygon candles before using cache replay.',
        ))

    congressional = list_congressional_trades(limit=5)
    congressional_counts = congressional_disclosure_counts()
    checks.append(_smoke_item(
        key='congressional_disclosures',
        label='Congressional disclosures',
        category='research_data',
        status='pass' if congressional.get('total', 0) else 'warning',
        rows=congressional.get('total', 0),
        detail=f"Local disclosure database contains House {congressional_counts.get('house', 0)} and Senate {congressional_counts.get('senate', 0)} rows.",
        action='Use the Congress tab to sync fresh disclosures and replay the stored ticker set.',
        sample={
            'counts': congressional_counts,
            'latest': (congressional.get('trades') or [{}])[0],
        },
    ))

    checks.append(_provider_smoke_check(
        provider=providers.get('etrade', {}),
        key='etrade_quote',
        label='E*TRADE quote and options data',
        category='live_market_data',
        missing_detail='E*TRADE OAuth is not fully configured.',
        missing_action='Save consumer key/secret, run OAuth connect, paste the verifier, then re-run this check.',
        fn=lambda: _smoke_quote(ETradeClient().get_quote('AAPL', detail_flag='ALL')),
    ))

    checks.append(_provider_smoke_check(
        provider=providers.get('tradovate', {}),
        key='tradovate_futures_candles',
        label='Tradovate futures candles',
        category='historical_candles',
        missing_detail='Tradovate username/password credentials are not configured.',
        missing_action='Save Tradovate username/password in Settings, then re-run this check.',
        fn=lambda: _smoke_candles(_load_tradovate_candles({
            'symbol': 'ES',
            'timeframe': '1min',
            'from': '2025-01-02',
            'to': '2025-01-02',
        })),
    ))

    checks.append(_provider_smoke_check(
        provider=providers.get('polygon', {}),
        key='polygon_stock_candles',
        label='Polygon stock candles',
        category='historical_candles',
        missing_detail='Polygon API key is not configured.',
        missing_action='Save POLYGON_API_KEY in Settings, then re-run this check.',
        fn=lambda: _smoke_candles(PolygonClient().get_aggregates(
            symbol='AAPL',
            timeframe='1d',
            start='2025-01-02',
            end='2025-01-10',
        )),
    ))

    return checks


def _run_smoke_check(key, label, category, expected, action, fn):
    try:
        result = fn()
        rows = result.get('rows', 0)
        status = 'pass' if rows > 0 else 'warning'
        detail = result.get('detail') or (f'{rows} rows returned.' if rows else 'No rows returned.')
        return _smoke_item(
            key=key,
            label=label,
            category=category,
            status=status,
            rows=rows,
            detail=detail,
            action=action,
            expected=expected,
            sample=result.get('sample'),
        )
    except Exception as exc:
        return _smoke_item(
            key=key,
            label=label,
            category=category,
            status='fail',
            detail=_safe_error(exc),
            action=action,
            expected=expected,
        )


def _provider_smoke_check(provider, key, label, category, missing_detail, missing_action, fn):
    if not provider.get('configured'):
        return _smoke_item(
            key=key,
            label=label,
            category=category,
            status='blocked',
            rows=0,
            detail=missing_detail,
            action=missing_action,
        )
    return _run_smoke_check(
        key=key,
        label=label,
        category=category,
        expected='Configured provider returns data from a lightweight read-only probe.',
        action='If this fails, re-save credentials and confirm the sandbox/live environment matches the account.',
        fn=fn,
    )


def _smoke_candles(candles, extra=None):
    sample = _candle_preview(candles)
    if extra:
        sample.update(extra)
    return {
        'rows': len(candles) if candles is not None else 0,
        'detail': f'{len(candles)} OHLCV rows returned.' if candles is not None else 'No candle frame returned.',
        'sample': sample,
    }


def _smoke_quote(payload):
    summary = summarize_quote_payload(payload)
    return {
        'rows': len(summary),
        'detail': f'{len(summary)} quote summaries returned.',
        'sample': summary[0] if summary else {},
    }


def _smoke_summary(checks):
    counts = {
        'pass': 0,
        'warning': 0,
        'blocked': 0,
        'fail': 0,
    }
    for check in checks:
        counts[check['status']] = counts.get(check['status'], 0) + 1
    return {
        **counts,
        'total': len(checks),
        'ready': counts.get('fail', 0) == 0 and counts.get('blocked', 0) == 0,
        'blocked_sources': [check['label'] for check in checks if check['status'] == 'blocked'],
        'failed_sources': [check['label'] for check in checks if check['status'] == 'fail'],
    }


def _smoke_item(key, label, category, status, rows=0, detail='', action='', expected='', sample=None):
    return {
        'key': key,
        'label': label,
        'category': category,
        'status': status,
        'rows': rows,
        'detail': detail,
        'action': action,
        'expected': expected,
        'sample': _json_ready(sample or {}),
    }


def _source_item(key, label, configured, status, rows=0, detail='', preview=None, next_steps=None):
    return {
        'key': key,
        'label': label,
        'configured': configured,
        'status': status,
        'rows': rows,
        'detail': detail,
        'preview': _json_ready(preview or {}),
        'next_steps': next_steps or [],
    }


def _candle_preview(candles):
    if candles is None or candles.empty:
        return {}
    first = candles.iloc[0]
    last = candles.iloc[-1]
    return {
        'first_timestamp': candles.index[0],
        'last_timestamp': candles.index[-1],
        'first_close': first.get('close'),
        'last_close': last.get('close'),
        'last_volume': last.get('volume'),
    }


def _safe_error(exc):
    text = str(exc)
    if not text:
        text = exc.__class__.__name__
    return text[:260]


def _load_backtest_candles(payload):
    source = payload.get('source', 'sample')
    if source == 'sample':
        return load_sample_candles(
            symbol=payload.get('symbol', 'ES'),
            timeframe=payload.get('timeframe', '1min'),
            start=payload.get('from'),
            end=payload.get('to'),
        )
    if source == 'coinbase':
        return CoinbaseClient().get_candles(
            product_id=payload.get('symbol', 'BTC-USD'),
            timeframe=payload.get('timeframe', '1d'),
            start=payload.get('from'),
            end=payload.get('to'),
        )
    if source == 'yahoo':
        return YahooClient().get_chart(
            symbol=payload.get('symbol', 'AAPL'),
            timeframe=payload.get('timeframe', '1d'),
            start=payload.get('from'),
            end=payload.get('to'),
        )
    if source == 'tradovate':
        return _load_tradovate_candles(payload)
    if source == 'polygon':
        return PolygonClient().get_aggregates(
            symbol=payload.get('symbol', 'AAPL'),
            timeframe=payload.get('timeframe', '1d'),
            start=payload.get('from'),
            end=payload.get('to'),
        )
    if source == 'cache':
        candles = load_cached_candles(
            symbol=payload.get('symbol', 'AAPL'),
            timeframe=payload.get('timeframe', '1d'),
            start=payload.get('from'),
            end=payload.get('to'),
        )
        if candles.empty:
            raise ValueError('No cached candles found for the requested symbol, timeframe, and date range.')
        return candles
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
