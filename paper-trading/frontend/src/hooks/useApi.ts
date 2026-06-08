import { useState } from 'react';

const apiBaseUrl = import.meta.env.VITE_BACKEND_URL ?? (import.meta.env.DEV ? 'http://localhost:5001' : '');

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const callApi = async <T>(url: string, options: RequestInit = {}): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
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
      setError(err instanceof Error ? err.message : String(err));
      return null;
    }
  };

  const clearError = () => setError(null);

  return { callApi, loading, error, clearError };
}
