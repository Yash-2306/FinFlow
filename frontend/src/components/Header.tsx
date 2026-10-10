import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-[#1a1d27]">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">FinFlow</h1>
          <p className="text-xs text-slate-400 leading-none">Anomaly Detection Pipeline</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-green-400 font-medium">Live</span>
        </div>
        <div className="text-right hidden sm:block">
          <p className="text-xs text-slate-400">Real-time monitoring</p>
          <p className="text-xs text-slate-500">{new Date().toLocaleDateString('en-US', { dateStyle: 'medium' })}</p>
        </div>
      </div>
    </header>
  );
};

export default Header;
