import React, { useEffect, useRef, useState } from 'react';
import type { Stats, RollingStats } from '../types';

interface StatsPanelProps {
  stats: Stats | null;
  rolling: RollingStats | null;
}

function useAnimatedNumber(target: number, duration = 600): number {
  const [value, setValue] = useState(target);
  const prev = useRef(target);
  const raf = useRef<number>(0);

  useEffect(() => {
    const start = prev.current;
    const diff = target - start;
    if (diff === 0) return;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = Math.min(now - startTime, duration);
      const progress = elapsed / duration;
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(start + diff * eased);
      if (elapsed < duration) {
        raf.current = requestAnimationFrame(animate);
      } else {
        setValue(target);
        prev.current = target;
      }
    };
    raf.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration]);

  return value;
}

interface KpiCardProps {
  title: string;
  value: number;
  format: (v: number) => string;
  icon: React.ReactNode;
  accent: string;
  danger?: boolean;
  rolling: RollingStats | null;
  rollingKey: 'count' | 'flagged';
}

const KpiCard: React.FC<KpiCardProps> = ({ title, value, format, icon, accent, danger, rolling, rollingKey }) => {
  const animated = useAnimatedNumber(value);
  return (
    <div className={`bg-[#1a1d27] rounded-2xl p-5 border ${danger ? 'border-red-500/30' : 'border-white/5'} flex flex-col gap-3 relative overflow-hidden`}>
      <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-10 ${accent}`} />
      <div className="flex items-start justify-between relative">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
          <p className={`text-2xl font-bold mt-1 ${danger ? 'text-red-400' : 'text-white'}`}>
            {format(animated)}
          </p>
        </div>
        <div className={`p-2.5 rounded-xl ${accent} bg-opacity-20`}>
          {icon}
        </div>
      </div>
      {rolling && (
        <div className="flex gap-2 relative">
          {[
            { label: '60s', val: rolling.last_60s[rollingKey] },
            { label: '5m', val: rolling.last_5min[rollingKey] },
            { label: '1h', val: rolling.last_1hr[rollingKey] },
          ].map(({ label, val }) => (
            <span key={label} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-xs text-slate-300">
              <span className="text-slate-500">{label}</span>
              <span className="font-semibold">{val}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const StatsPanel: React.FC<StatsPanelProps> = ({ stats, rolling }) => {
  const totalTxns = stats?.total_transactions ?? 0;
  const totalFlagged = stats?.total_flagged ?? 0;
  const totalVolume = stats?.total_volume ?? 0;
  const flagRate = stats?.flag_rate ?? 0;

  const animatedTxns = useAnimatedNumber(totalTxns);
  const animatedFlagged = useAnimatedNumber(totalFlagged);
  const animatedVolume = useAnimatedNumber(totalVolume);
  const animatedFlagRate = useAnimatedNumber(flagRate);

  const cards = [
    {
      title: 'Total Transactions',
      animated: animatedTxns,
      format: (v: number) => Math.round(v).toLocaleString(),
      icon: (
        <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5h18M3 12h18M3 16.5h18" />
        </svg>
      ),
      accent: 'bg-indigo-500',
      danger: false,
      rollingKey: 'count' as const,
    },
    {
      title: 'Flagged Transactions',
      animated: animatedFlagged,
      format: (v: number) => Math.round(v).toLocaleString(),
      icon: (
        <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l1.664 1.664M21 21l-1.5-1.5m-5.485-1.242L12 17.25 4.5 21V8.742m.164-4.078a2.15 2.15 0 011.743-1.342 48.507 48.507 0 0111.186 0c1.1.128 1.907 1.077 1.907 2.185V19.5M4.664 4.664L19.5 19.5" />
        </svg>
      ),
      accent: 'bg-red-500',
      danger: flagRate > 5,
      rollingKey: 'flagged' as const,
    },
    {
      title: 'Total Volume',
      animated: animatedVolume,
      format: (v: number) => `$${(v / 1000).toFixed(1)}K`,
      icon: (
        <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33" />
        </svg>
      ),
      accent: 'bg-green-500',
      danger: false,
      rollingKey: 'count' as const,
    },
    {
      title: 'Flag Rate',
      animated: animatedFlagRate,
      format: (v: number) => `${v.toFixed(1)}%`,
      icon: (
        <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      ),
      accent: 'bg-amber-500',
      danger: flagRate > 5,
      rollingKey: 'flagged' as const,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <KpiCard
          key={card.title}
          title={card.title}
          value={card.animated}
          format={card.format}
          icon={card.icon}
          accent={card.accent}
          danger={card.danger}
          rolling={rolling}
          rollingKey={card.rollingKey}
        />
      ))}
    </div>
  );
};

export default StatsPanel;
