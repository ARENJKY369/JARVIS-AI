import { useState, useCallback } from 'react';

const API_BASE = '/api/v1';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async <T,>(path: string, options?: RequestInit): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<T>(path, options);
      return data;
    } catch (e: any) {
      setError(e.message || 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { request, loading, error };
}

export { apiFetch };
