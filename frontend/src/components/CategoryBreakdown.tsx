import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import type { CategoryStat } from '../types';

interface CategoryBreakdownProps {
  categories: CategoryStat[];
}

function anomalyColor(cat: CategoryStat): string {
  const rate = cat.count > 0 ? cat.anomaly_count / cat.count : 0;
  if (rate < 0.1) return '#22c55e';
  if (rate < 0.25) return '#f59e0b';
  return '#ef4444';
}

const CustomTooltip = ({ active, payload }: {
  active?: boolean;
  payload?: Array<{ payload: CategoryStat }>;
}) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const rate = d.count > 0 ? ((d.anomaly_count / d.count) * 100).toFixed(1) : '0.0';
  return (
    <div className="bg-[#1a1d27] border border-white/10 rounded-xl px-4 py-3 shadow-2xl text-sm">
      <p className="font-semibold text-white mb-1 capitalize">{d.category}</p>
      <div className="space-y-0.5 text-slate-300 text-xs">
        <p>Volume: <span className="text-white font-medium">${d.total_volume.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></p>
        <p>Transactions: <span className="text-white font-medium">{d.count}</span></p>
        <p>Anomalies: <span className="text-red-400 font-medium">{d.anomaly_count} ({rate}%)</span></p>
        <p>Avg amount: <span className="text-white font-medium">${d.avg_amount.toFixed(2)}</span></p>
      </div>
    </div>
  );
};

const CategoryBreakdown: React.FC<CategoryBreakdownProps> = ({ categories }) => {
  const sorted = [...categories].sort((a, b) => b.total_volume - a.total_volume).slice(0, 8);

  return (
    <div className="bg-[#1a1d27] rounded-2xl border border-white/5 p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Category Breakdown</h2>
        <p className="text-xs text-slate-500 mt-0.5">Volume by merchant category</p>
      </div>
      <div className="flex gap-4 mb-3 text-xs text-slate-400">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-green-500 inline-block" /> Low risk</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-amber-500 inline-block" /> Medium</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-red-500 inline-block" /> High</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={sorted} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: '#64748b', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={80}
            tickFormatter={(v: string) => v.charAt(0).toUpperCase() + v.slice(1)}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="total_volume" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {sorted.map((entry) => (
              <Cell key={entry.category} fill={anomalyColor(entry)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CategoryBreakdown;
