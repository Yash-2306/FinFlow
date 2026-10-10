import type { Transaction, Stats, CategoryStat, RollingStats, RiskBucket } from './types';

export const API_BASE = (import.meta.env.VITE_API_URL as string) || '/api';

async function apiFetch<T>(path: string, params?: Record<string, string | number | boolean>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

export function fetchStats(): Promise<Stats> {
  return apiFetch<Stats>('/analytics/stats');
}

export function fetchCategories(): Promise<CategoryStat[]> {
  return apiFetch<CategoryStat[]>('/analytics/categories');
}

export function fetchRolling(): Promise<RollingStats> {
  return apiFetch<RollingStats>('/analytics/rolling');
}

export function fetchRiskDistribution(): Promise<RiskBucket[]> {
  return apiFetch<RiskBucket[]>('/analytics/risk-distribution');
}

export function fetchTransactions(
  limit = 20,
  offset = 0,
  flaggedOnly = false
): Promise<{ transactions: Transaction[]; total: number }> {
  return apiFetch<{ transactions: Transaction[]; total: number }>('/transactions', {
    limit,
    offset,
    flagged_only: flaggedOnly,
  });
}

export function startTransactionStream(callbacks: {
  onTransaction: (tx: Transaction) => void;
  onError: (err: string) => void;
}): AbortController {
  const controller = new AbortController();
  let retryTimeout: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (controller.signal.aborted) return;

    const url = `${API_BASE}/transactions/stream`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const tx = JSON.parse(e.data) as Transaction;
        callbacks.onTransaction(tx);
      } catch {
        callbacks.onError('Failed to parse transaction data');
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      if (!controller.signal.aborted) {
        callbacks.onError('SSE stream disconnected, reconnecting...');
        retryTimeout = setTimeout(connect, 3000);
      }
    };

    controller.signal.addEventListener('abort', () => {
      eventSource.close();
      if (retryTimeout) clearTimeout(retryTimeout);
    });
  }

  connect();
  return controller;
}
