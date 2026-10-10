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
import type { RiskBucket } from '../types';

interface RiskDistributionProps {
  buckets: RiskBucket[];
}

const BUCKET_COLORS: Record<string, string> = {
  '0-0.2': '#22c55e',
  '0.2-0.4': '#84cc16',
  '0.4-0.6': '#f59e0b',
  '0.6-0.8': '#f97316',
  '0.8-1.0': '#ef4444',
};

function bucketColor(range: string): string {
  return BUCKET_COLORS[range] ?? '#6366f1';
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#1a1d27] border border-white/10 rounded-xl px-4 py-3 shadow-2xl text-sm">
      <p className="text-xs text-slate-400 mb-1">Risk Score: <span className="text-white font-medium">{label}</span></p>
      <p className="text-white">
        Transactions: <span className="font-semibold">{payload[0].value.toLocaleString()}</span>
      </p>
    </div>
  );
};

const RiskDistribution: React.FC<RiskDistributionProps> = ({ buckets }) => {
  return (
    <div className="bg-[#1a1d27] rounded-2xl border border-white/5 p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Risk Distribution</h2>
        <p className="text-xs text-slate-500 mt-0.5">Transaction count by risk score bucket</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={buckets} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
          <XAxis
            dataKey="range"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
            {buckets.map((b) => (
              <Cell key={b.range} fill={bucketColor(b.range)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RiskDistribution;
