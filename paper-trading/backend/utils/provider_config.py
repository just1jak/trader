import os
from pathlib import Path


ENV_PATH = Path(os.getenv('PROVIDER_ENV_PATH', Path(__file__).resolve().parents[2] / '.env'))

PROVIDERS = {
    'etrade': {
        'label': 'E*TRADE',
        'description': 'Read-only quote, expiration, and option-chain market data.',
        'fields': {
            'ETRADE_ENV': {'label': 'Environment', 'secret': False, 'default': 'sandbox'},
            'ETRADE_CONSUMER_KEY': {'label': 'Consumer key', 'secret': True},
            'ETRADE_CONSUMER_SECRET': {'label': 'Consumer secret', 'secret': True},
            'ETRADE_ACCESS_TOKEN': {'label': 'Access token', 'secret': True},
            'ETRADE_ACCESS_TOKEN_SECRET': {'label': 'Access token secret', 'secret': True},
        },
        'required': [
            'ETRADE_CONSUMER_KEY',
            'ETRADE_CONSUMER_SECRET',
            'ETRADE_ACCESS_TOKEN',
            'ETRADE_ACCESS_TOKEN_SECRET',
        ],
    },
    'tradovate': {
        'label': 'Tradovate',
        'description': 'Historical futures candle source for backtests.',
        'fields': {
            'TRADOVATE_BASE_URL': {'label': 'Base URL', 'secret': False, 'default': 'https://demo.tradovateapi.com/v1'},
            'TRADOVATE_API_KEY': {'label': 'API key / username', 'secret': True},
            'TRADOVATE_API_SECRET': {'label': 'API secret / password', 'secret': True},
        },
        'required': ['TRADOVATE_API_KEY', 'TRADOVATE_API_SECRET'],
    },
    'polygon': {
        'label': 'Polygon',
        'description': 'Reserved market-data provider slot. Stored here but not used by backtests yet.',
        'fields': {
            'POLYGON_API_KEY': {'label': 'API key', 'secret': True},
        },
        'required': ['POLYGON_API_KEY'],
    },
}


def provider_status():
    env_values = _read_env_file()
    providers = []
    for provider_key, provider in PROVIDERS.items():
        fields = []
        for env_key, meta in provider['fields'].items():
            value = env_values.get(env_key) or os.getenv(env_key) or meta.get('default', '')
            fields.append({
                'key': env_key,
                'label': meta['label'],
                'secret': meta.get('secret', False),
                'configured': bool(value),
                'value': _masked(value) if meta.get('secret') else value,
            })

        providers.append({
            'key': provider_key,
            'label': provider['label'],
            'description': provider['description'],
            'configured': all(env_values.get(key) or os.getenv(key) for key in provider['required']),
            'fields': fields,
        })
    return providers


def save_provider_settings(provider_key, values):
    if provider_key not in PROVIDERS:
        raise ValueError(f'Unsupported provider: {provider_key}')

    provider = PROVIDERS[provider_key]
    allowed_keys = set(provider['fields'])
    updates = {
        key: str(value).strip()
        for key, value in (values or {}).items()
        if key in allowed_keys and value not in (None, '')
    }
    if not updates:
        return provider_status()

    env_values = _read_env_file()
    env_values.update(updates)
    _write_env_file(env_values)

    for key, value in updates.items():
        os.environ[key] = value

    return provider_status()


def apply_to_flask_config(app):
    env_values = _read_env_file()
    for provider in PROVIDERS.values():
        for key, meta in provider['fields'].items():
            value = env_values.get(key) or os.getenv(key) or meta.get('default')
            if value is not None:
                app.config[key] = value

    etrade_env = str(app.config.get('ETRADE_ENV', 'sandbox')).lower()
    app.config['ETRADE_BASE_URL'] = (
        env_values.get('ETRADE_BASE_URL')
        or os.getenv('ETRADE_BASE_URL')
        or ('https://apisb.etrade.com' if etrade_env == 'sandbox' else 'https://api.etrade.com')
    )


def _read_env_file():
    if not ENV_PATH.exists():
        return {}

    values = {}
    for line in ENV_PATH.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue
        key, value = stripped.split('=', 1)
        values[key.strip()] = value.strip()
    return values


def _write_env_file(values):
    existing_lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    seen = set()
    output = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            output.append(line)
            continue

        key, _ = stripped.split('=', 1)
        key = key.strip()
        if key in values:
            output.append(f'{key}={values[key]}')
            seen.add(key)
        else:
            output.append(line)

    for key, value in values.items():
        if key not in seen:
            output.append(f'{key}={value}')

    ENV_PATH.write_text('\n'.join(output) + '\n')


def _masked(value):
    if not value:
        return ''
    if len(value) <= 8:
        return '****'
    return f'{value[:4]}****{value[-4:]}'
