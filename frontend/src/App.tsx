import React, { useState, useEffect, useRef, useCallback } from 'react';
import Header from './components/Header';
import StatsPanel from './components/StatsPanel';
import LiveFeed from './components/LiveFeed';
import AnomalyChart from './components/AnomalyChart';
import CategoryBreakdown from './components/CategoryBreakdown';
import RiskDistribution from './components/RiskDistribution';
import TransactionTable from './components/TransactionTable';
import {
  fetchStats,
  fetchCategories,
  fetchRolling,
  fetchRiskDistribution,
  startTransactionStream,
} from './api';
import type { Stats, CategoryStat, RollingStats, RiskBucket, Transaction } from './types';

interface ChartPoint {
  time: string;
  total: number;
  flagged: number;
}

type Tab = 'dashboard' | 'history';

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [stats, setStats] = useState<Stats | null>(null);
  const [categories, setCategories] = useState<CategoryStat[]>([]);
  const [rolling, setRolling] = useState<RollingStats | null>(null);
  const [riskBuckets, setRiskBuckets] = useState<RiskBucket[]>([]);
  const [liveFeed, setLiveFeed] = useState<Transaction[]>([]);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);

  const windowRef = useRef<{ total: number; flagged: number }>({ total: 0, flagged: 0 });
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadAnalytics = useCallback(async () => {
    try {
      const [s, c, r, rd] = await Promise.all([
        fetchStats(),
        fetchCategories(),
        fetchRolling(),
        fetchRiskDistribution(),
      ]);
      setStats(s);
      setCategories(c);
      setRolling(r);
      setRiskBuckets(rd);
    } catch {
      // silently retry on next interval
    }
  }, []);

  // Initial load + periodic refresh every 10s
  useEffect(() => {
    void loadAnalytics();
    const interval = setInterval(() => void loadAnalytics(), 10000);
    return () => clearInterval(interval);
  }, [loadAnalytics]);

  // Chart ticker every 3 seconds
  useEffect(() => {
    tickRef.current = setInterval(() => {
      const { total, flagged } = windowRef.current;
      windowRef.current = { total: 0, flagged: 0 };
      const point: ChartPoint = { time: formatTime(new Date()), total, flagged };
      setChartData((prev) => {
        const next = [...prev, point];
        return next.length > 60 ? next.slice(next.length - 60) : next;
      });
    }, 3000);
    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, []);

  // SSE stream
  useEffect(() => {
    const ctrl = startTransactionStream({
      onTransaction: (tx) => {
        setLiveFeed((prev) => [tx, ...prev].slice(0, 20));
        windowRef.current.total += 1;
        if (tx.is_flagged) windowRef.current.flagged += 1;
      },
      onError: (err) => setStreamError(err),
    });
    return () => ctrl.abort();
  }, []);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    {
      id: 'dashboard',
      label: 'Live Dashboard',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
        </svg>
      ),
    },
    {
      id: 'history',
      label: 'Transaction History',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-[#0f1117] text-white font-sans">
      <Header />

      {/* Tab bar */}
      <div className="px-6 pt-4 border-b border-white/5">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all border-b-2 ${
                activeTab === tab.id
                  ? 'text-indigo-400 border-indigo-500 bg-indigo-500/5'
                  : 'text-slate-400 border-transparent hover:text-slate-200 hover:border-white/20'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stream error banner */}
      {streamError && (
        <div className="mx-6 mt-4 px-4 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          {streamError}
        </div>
      )}

      {/* Dashboard tab */}
      {activeTab === 'dashboard' && (
        <main className="p-6 space-y-5">
          <StatsPanel stats={stats} rolling={rolling} />
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
            <div className="xl:col-span-2">
              <AnomalyChart data={chartData} />
            </div>
            <div>
              <LiveFeed transactions={liveFeed} />
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <CategoryBreakdown categories={categories} />
            <RiskDistribution buckets={riskBuckets} />
          </div>
        </main>
      )}

      {/* History tab */}
      {activeTab === 'history' && (
        <main className="p-6">
          <TransactionTable
            flaggedOnly={flaggedOnly}
            onToggleFlagged={() => setFlaggedOnly((f) => !f)}
          />
        </main>
      )}
    </div>
  );
};

export default App;
