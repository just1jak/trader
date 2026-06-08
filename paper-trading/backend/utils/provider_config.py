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
        'description': 'Historical futures candle source for backtests. Uses Tradovate username/password plus optional API cid/sec fields.',
        'fields': {
            'TRADOVATE_BASE_URL': {'label': 'Base URL', 'secret': False, 'default': 'https://demo.tradovateapi.com/v1'},
            'TRADOVATE_USERNAME': {'label': 'Username', 'secret': True},
            'TRADOVATE_PASSWORD': {'label': 'Password / API password', 'secret': True},
            'TRADOVATE_APP_ID': {'label': 'App ID', 'secret': False, 'default': 'papertradingwebapp'},
            'TRADOVATE_APP_VERSION': {'label': 'App version', 'secret': False, 'default': '1.0.0'},
            'TRADOVATE_CID': {'label': 'Client app id / cid', 'secret': True},
            'TRADOVATE_SECRET': {'label': 'API secret / sec', 'secret': True},
            'TRADOVATE_DEVICE_ID': {'label': 'Device ID', 'secret': False, 'default': 'papertrading-web'},
            'TRADOVATE_API_KEY': {'label': 'Legacy username fallback', 'secret': True},
            'TRADOVATE_API_SECRET': {'label': 'Legacy password fallback', 'secret': True},
        },
        'required': ['TRADOVATE_USERNAME', 'TRADOVATE_PASSWORD'],
        'legacy_required': ['TRADOVATE_API_KEY', 'TRADOVATE_API_SECRET'],
    },
    'polygon': {
        'label': 'Polygon',
        'description': 'Historical stock and options aggregate bars for backtests.',
        'fields': {
            'POLYGON_BASE_URL': {'label': 'Base URL', 'secret': False, 'default': 'https://api.polygon.io'},
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
                'configured': _has_real_value(value, allow_default=True),
                'value': _masked(value) if meta.get('secret') else value,
            })

        providers.append({
            'key': provider_key,
            'label': provider['label'],
            'description': provider['description'],
            'configured': _provider_configured(provider, env_values),
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


def clear_provider_settings(provider_key, keys):
    if provider_key not in PROVIDERS:
        raise ValueError(f'Unsupported provider: {provider_key}')

    provider = PROVIDERS[provider_key]
    allowed_keys = set(provider['fields'])
    clear_keys = [key for key in (keys or []) if key in allowed_keys]
    if not clear_keys:
        return provider_status()

    env_values = _read_env_file()
    for key in clear_keys:
        env_values.pop(key, None)
        os.environ.pop(key, None)

    _write_env_file(env_values, removed_keys=set(clear_keys))
    return provider_status()


def apply_to_flask_config(app):
    env_values = _read_env_file()
    for provider in PROVIDERS.values():
        for key, meta in provider['fields'].items():
            value = env_values.get(key) or os.getenv(key) or meta.get('default')
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


def _write_env_file(values, removed_keys=None):
    existing_lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    removed_keys = removed_keys or set()
    seen = set()
    output = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            output.append(line)
            continue

        key, _ = stripped.split('=', 1)
        key = key.strip()
        if key in removed_keys:
            continue
        if key in values:
            output.append(f'{key}={values[key]}')
            seen.add(key)
        else:
            output.append(line)

    for key, value in values.items():
        if key not in seen:
            output.append(f'{key}={value}')

    ENV_PATH.write_text('\n'.join(output) + '\n')


def _provider_configured(provider, env_values):
    primary = all(_has_real_value(env_values.get(key) or os.getenv(key)) for key in provider['required'])
    legacy = provider.get('legacy_required')
    if primary or not legacy:
        return primary
    return all(_has_real_value(env_values.get(key) or os.getenv(key)) for key in legacy)


def _has_real_value(value, allow_default=False):
    if value is None:
        return False
    normalized = str(value).strip()
    if not normalized:
        return False
    if allow_default and normalized.startswith(('http://', 'https://')):
        return True

    lowered = normalized.lower()
    placeholder_tokens = (
        'your_',
        '_here',
        'change-me',
        'changeme',
        'change_in_production',
        'placeholder',
        'example',
    )
    return not any(token in lowered for token in placeholder_tokens)


def _masked(value):
    if not value:
        return ''
    if len(value) <= 8:
        return '****'
    return f'{value[:4]}****{value[-4:]}'
