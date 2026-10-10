import React, { useEffect, useRef } from 'react';
import type { Transaction } from '../types';
import RiskBadge from './RiskBadge';

interface LiveFeedProps {
  transactions: Transaction[];
}

const CATEGORY_EMOJI: Record<string, string> = {
  groceries: '🛒',
  entertainment: '🎬',
  travel: '✈️',
  dining: '🍽️',
  electronics: '💻',
  healthcare: '🏥',
  fuel: '⛽',
  clothing: '👗',
  utilities: '💡',
  finance: '🏦',
  gaming: '🎮',
  sports: '⚽',
  beauty: '💅',
  education: '📚',
  default: '💳',
};

function getEmoji(category: string): string {
  return CATEGORY_EMOJI[category.toLowerCase()] ?? CATEGORY_EMOJI.default;
}

function timeAgo(timestamp: string): string {
  const diff = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

const LiveFeed: React.FC<LiveFeedProps> = ({ transactions }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const prevLength = useRef(transactions.length);

  useEffect(() => {
    prevLength.current = transactions.length;
  }, [transactions.length]);

  return (
    <div className="bg-[#1a1d27] rounded-2xl border border-white/5 flex flex-col h-full max-h-[560px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <h2 className="text-sm font-semibold text-white">Live Feed</h2>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-slate-400">{transactions.length} shown</span>
        </div>
      </div>
      <div ref={containerRef} className="flex-1 overflow-y-auto divide-y divide-white/5 scrollbar-thin">
        {transactions.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-slate-500 text-sm gap-2">
            <span className="text-2xl">📡</span>
            <span>Waiting for transactions…</span>
          </div>
        )}
        {transactions.map((tx, idx) => (
          <div
            key={tx.id}
            className={`flex items-center gap-3 px-4 py-3 transition-colors hover:bg-white/5 ${
              tx.is_flagged ? 'border-l-2 border-red-500' : 'border-l-2 border-transparent'
            } ${idx === 0 ? 'animate-fadeIn' : ''}`}
          >
            <div className="text-xl flex-shrink-0 w-8 text-center">
              {getEmoji(tx.merchant_category)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-white truncate">{tx.merchant_name}</p>
                <span className="text-sm font-semibold text-white whitespace-nowrap">
                  ${tx.amount.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2 mt-0.5">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-xs text-slate-500 truncate">{tx.location_city}</span>
                  {tx.is_flagged && (
                    <span className="text-xs text-red-400 font-medium">⚠ Flagged</span>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <RiskBadge score={tx.risk_score} showLabel={false} />
                  <span className="text-xs text-slate-500">{timeAgo(tx.timestamp)}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LiveFeed;
