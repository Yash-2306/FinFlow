import React, { useState, useEffect, useCallback } from 'react';
import type { Transaction } from '../types';
import { fetchTransactions } from '../api';
import RiskBadge from './RiskBadge';

const PAGE_SIZE = 20;

type SortKey = 'amount' | 'risk_score' | 'timestamp';
type SortDir = 'asc' | 'desc';

interface TransactionTableProps {
  flaggedOnly: boolean;
  onToggleFlagged: () => void;
}

function truncateId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 6)}…${id.slice(-4)}` : id;
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

const TransactionTable: React.FC<TransactionTableProps> = ({ flaggedOnly, onToggleFlagged }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<SortKey>('timestamp');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTransactions(PAGE_SIZE, page * PAGE_SIZE, flaggedOnly);
      setTransactions(result.transactions);
      setTotal(result.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  }, [page, flaggedOnly]);

  useEffect(() => {
    void load();
  }, [load]);

  // Reset page when filter changes
  useEffect(() => {
    setPage(0);
  }, [flaggedOnly]);

  const sorted = [...transactions].sort((a, b) => {
    let av: number, bv: number;
    if (sortKey === 'amount') { av = a.amount; bv = b.amount; }
    else if (sortKey === 'risk_score') { av = a.risk_score; bv = b.risk_score; }
    else { av = new Date(a.timestamp).getTime(); bv = new Date(b.timestamp).getTime(); }
    return sortDir === 'asc' ? av - bv : bv - av;
  });

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <span className="text-slate-600 ml-1">⇅</span>;
    return <span className="text-indigo-400 ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="bg-[#1a1d27] rounded-2xl border border-white/5 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div>
          <h2 className="text-sm font-semibold text-white">Transaction History</h2>
          <p className="text-xs text-slate-500 mt-0.5">{total.toLocaleString()} records</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleFlagged}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              flaggedOnly
                ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l1.664 1.664M21 21l-1.5-1.5m-5.485-1.242L12 17.25 4.5 21V8.742m.164-4.078a2.15 2.15 0 011.743-1.342 48.507 48.507 0 0111.186 0c1.1.128 1.907 1.077 1.907 2.185V19.5M4.664 4.664L19.5 19.5" />
            </svg>
            {flaggedOnly ? 'Flagged Only' : 'All Transactions'}
          </button>
          <button
            onClick={() => void load()}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30 transition-all disabled:opacity-50"
          >
            {loading ? '⟳' : '↻'} Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5">
              {['ID', 'Customer', 'Category', 'Merchant', 'Amount', 'Location', 'Risk Score', 'Status', 'Time'].map((col) => {
                const sortable = col === 'Amount' ? 'amount' : col === 'Risk Score' ? 'risk_score' : col === 'Time' ? 'timestamp' : null;
                return (
                  <th
                    key={col}
                    onClick={sortable ? () => handleSort(sortable as SortKey) : undefined}
                    className={`px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider whitespace-nowrap ${
                      sortable ? 'cursor-pointer hover:text-white select-none' : ''
                    }`}
                  >
                    {col}
                    {sortable && <SortIcon col={sortable as SortKey} />}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading && transactions.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center text-slate-500">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                    Loading…
                  </div>
                </td>
              </tr>
            ) : sorted.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center text-slate-500">No transactions found.</td>
              </tr>
            ) : (
              sorted.map((tx) => (
                <React.Fragment key={tx.id}>
                  <tr
                    onClick={() => setExpandedId(expandedId === tx.id ? null : tx.id)}
                    className={`cursor-pointer transition-colors hover:bg-white/5 ${
                      tx.is_flagged ? 'bg-red-500/5' : ''
                    } ${expandedId === tx.id ? 'bg-indigo-500/10' : ''}`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">{truncateId(tx.id)}</td>
                    <td className="px-4 py-3 text-slate-300 font-mono text-xs">{truncateId(tx.customer_id)}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full bg-white/5 text-slate-300 text-xs capitalize">
                        {tx.merchant_category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white font-medium max-w-[140px] truncate">{tx.merchant_name}</td>
                    <td className="px-4 py-3 text-white font-semibold">${tx.amount.toFixed(2)}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                      {tx.location_city}, {tx.location_country}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge score={tx.risk_score} />
                    </td>
                    <td className="px-4 py-3">
                      {tx.is_flagged ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 text-xs font-medium border border-red-500/25">
                          ⚠ Flagged
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20">
                          ✓ Clear
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{formatTime(tx.timestamp)}</td>
                  </tr>
                  {expandedId === tx.id && (
                    <tr className="bg-indigo-500/5">
                      <td colSpan={9} className="px-6 py-4">
                        <div className="flex flex-wrap gap-3 items-start">
                          <div>
                            <p className="text-xs text-slate-500 mb-1 font-medium uppercase tracking-wider">Transaction ID</p>
                            <p className="font-mono text-xs text-indigo-400">{tx.id}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 mb-1 font-medium uppercase tracking-wider">Type</p>
                            <p className="text-xs text-white capitalize">{tx.transaction_type}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 mb-1 font-medium uppercase tracking-wider">Currency</p>
                            <p className="text-xs text-white">{tx.currency}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 mb-1 font-medium uppercase tracking-wider">Risk Score</p>
                            <p className="text-xs text-white font-mono">{tx.risk_score.toFixed(4)}</p>
                          </div>
                          {tx.flag_reasons.length > 0 && (
                            <div>
                              <p className="text-xs text-slate-500 mb-1 font-medium uppercase tracking-wider">Flag Reasons</p>
                              <div className="flex flex-wrap gap-1">
                                {tx.flag_reasons.map((r) => (
                                  <span key={r} className="px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 text-xs border border-red-500/25 capitalize">
                                    {r.replace(/_/g, ' ')}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-5 py-4 border-t border-white/5">
        <p className="text-xs text-slate-500">
          Page {page + 1} of {Math.max(totalPages, 1)} · {total.toLocaleString()} total
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0 || loading}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-slate-300 border border-white/10 hover:bg-white/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Prev
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1 || loading}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-slate-300 border border-white/10 hover:bg-white/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionTable;
