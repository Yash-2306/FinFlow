import React from 'react';

interface RiskBadgeProps {
  score: number;
  showLabel?: boolean;
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ score, showLabel = true }) => {
  if (score < 0.3) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
        {showLabel && 'LOW'}
        {!showLabel && score.toFixed(2)}
      </span>
    );
  }
  if (score <= 0.65) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
        {showLabel && 'MEDIUM'}
        {!showLabel && score.toFixed(2)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" />
      {showLabel && 'HIGH'}
      {!showLabel && score.toFixed(2)}
    </span>
  );
};

export default RiskBadge;
