import { useState } from 'react';

const rawBackendUrl = import.meta.env.VITE_BACKEND_URL?.trim() || '';

function resolveApiBaseUrl() {
  if (!rawBackendUrl) {
    return '';
  }

  try {
    const parsed = new URL(rawBackendUrl, window.location.origin);
    const backendHost = parsed.hostname;
    const currentHost = window.location.hostname;

    const isLoopback = ['localhost', '127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(backendHost);
    const isCurrentHost = backendHost === currentHost;
    const hasDomain = backendHost.includes('.');
    const looksLikeContainerAlias = backendHost && !hasDomain && backendHost !== currentHost && !isLoopback;

    if (looksLikeContainerAlias) {
      return '';
    }

    if (parsed.protocol.startsWith('http') && (isCurrentHost || isLoopback || hasDomain)) {
      return parsed.href.endsWith('/') ? parsed.href.slice(0, -1) : parsed.href;
    }

    return '';
  } catch {
    return '';
  }
}

const apiBaseUrl = resolveApiBaseUrl();

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  type ApiRequestOptions = RequestInit & {
    silent?: boolean;
    onError?: (message: string) => void;
  };

  const callApi = async <T>(url: string, options: ApiRequestOptions = {}): Promise<T | null> => {
    const { silent = false, onError, ...fetchOptions } = options;

    setLoading(true);
    if (!silent) {
      setError(null);
    }

    try {
      const response = await fetch(`${apiBaseUrl}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
        ...fetchOptions,
      });
      if (!response.ok) {
        let message = `API error: ${response.status}`;
        const text = await response.text();
        try {
          const payload = text ? JSON.parse(text) : null;
          if (payload?.error) {
            message = String(payload.error);
          } else if (payload?.message) {
            message = String(payload.message);
          }
        } catch {
          if (text) message = text.slice(0, 240);
        }
        throw new Error(message);
      }
      const data = await response.json();
      setLoading(false);
      return data;
    } catch (err) {
      setLoading(false);
      const message = err instanceof Error ? err.message : String(err);
      if (typeof onError === 'function') {
        onError(message);
      }
      if (!silent) {
        setError(message);
      }
      return null;
    }
  };

  const clearError = () => setError(null);

  return { callApi, loading, error, clearError };
}
