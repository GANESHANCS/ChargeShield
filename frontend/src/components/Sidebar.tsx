import React from 'react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  backendOnline: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ backendOnline }) => {
  const navItems = [
    { num: '01', label: 'RISK_OVERVIEW', path: '/' },
    { num: '02', label: 'REVIEW_QUEUE', path: '/queue' },
    { num: '03', label: 'CASES', path: '/cases' },
    { num: '04', label: 'MODEL', path: '/model' },
    { num: '05', label: 'ANALYTICS', path: '/analytics' },
    { num: '06', label: 'AUDIT', path: '/audit' },
  ];

  return (
    <aside className="w-64 bg-black border-r border-white/12 flex flex-col justify-between p-6 z-10 shrink-0 select-none">
      <div>
        {/* Brand Logo Header */}
        <div className="pb-6 mb-8 border-b border-white/12">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 bg-[#AFDDFF] inline-block" />
            <h1 className="text-lg font-display font-bold tracking-tight text-white uppercase">
              CHARGESHIELD <span className="text-[#AFDDFF]/80 font-normal">//</span>
            </h1>
          </div>
          <p className="text-[10px] font-mono text-white/40 uppercase tracking-widest mt-1">
            AI Risk Operations Platform
          </p>
        </div>

        {/* Minimal Numbered Navigation */}
        <nav className="space-y-3 font-mono text-xs">
          {navItems.map((item) => {
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 py-2 px-3 transition-all duration-200 border-l-2 ${
                    isActive
                      ? 'border-[#AFDDFF] bg-white/[0.03] text-white font-medium'
                      : 'border-transparent text-white/60 hover:text-[#AFDDFF] hover:border-white/20'
                  }`
                }
              >
                <span className="text-[#AFDDFF]/80 text-[11px] font-mono">{item.num}.</span>
                <span className="tracking-wider">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status & Analyst Identity */}
      <div className="space-y-4 pt-6 border-t border-white/12 font-mono text-xs">
        {/* Compact Subsystem Health Summary */}
        <div className="p-3 bg-white/[0.02] border border-white/10 space-y-2">
          <div className="text-[9px] text-white/40 uppercase tracking-widest">
            [ SYSTEM_STATUS ]
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-white/60">BACKEND API</span>
            <span className={`font-mono text-[10px] ${backendOnline ? 'text-[#9FE6C1]' : 'text-[#E68A8A]'}`}>
              {backendOnline ? '● ONLINE' : '✖ OFFLINE'}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-white/60">ML ENGINE</span>
            <span className="font-mono text-[10px] text-[#9FE6C1]">● READY</span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-white/60">EVIDENCE VERIFIER</span>
            <span className="font-mono text-[10px] text-[#9FE6C1]">● ACTIVE</span>
          </div>
        </div>

        {/* User Identity */}
        <div className="flex items-center gap-3 px-3 py-2 bg-white/[0.02] border border-white/10 text-xs">
          <div className="h-6 w-6 bg-white/10 flex items-center justify-center text-[#AFDDFF] font-mono text-[10px] border border-white/20">
            SA
          </div>
          <div className="overflow-hidden">
            <div className="font-mono text-[11px] text-white truncate">analyst_sarah_01</div>
            <div className="text-[9px] text-white/40 font-mono uppercase">Risk Analyst</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
