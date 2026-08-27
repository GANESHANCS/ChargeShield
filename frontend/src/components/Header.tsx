import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title: string;
  subtitle: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  const [searchId, setSearchId] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchId.trim()) {
      const cleanId = searchId.trim().toUpperCase();
      navigate(`/cases/${cleanId}`);
    }
  };

  return (
    <header className="bg-black/90 border-b border-white/12 px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-md sticky top-0 z-20">
      {/* Title & Subtitle */}
      <div>
        <h1 className="text-xl font-display font-bold tracking-tight text-white uppercase">{title}</h1>
        <p className="text-xs font-mono text-white/50 mt-0.5">{subtitle}</p>
      </div>

      {/* Right Controls & Operational Status Strip */}
      <div className="flex flex-wrap items-center gap-6">
        {/* Compact Operational Status Strip */}
        <div className="hidden lg:flex items-center gap-4 text-[10px] font-mono text-white/60 border border-white/12 px-3 py-1.5 bg-white/[0.02]">
          <div className="flex items-center gap-1.5 text-[#9FE6C1]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#9FE6C1] animate-pulse" />
            <span>[ SYSTEM ONLINE ]</span>
          </div>
          <span className="text-white/20">|</span>
          <div className="flex items-center gap-1">
            <span className="text-white/40">API</span>
            <span className="text-[#9FE6C1]">CONNECTED</span>
          </div>
          <span className="text-white/20">|</span>
          <div className="flex items-center gap-1">
            <span className="text-white/40">DB</span>
            <span className="text-[#9FE6C1]">CONNECTED</span>
          </div>
          <span className="text-white/20">|</span>
          <div className="flex items-center gap-1">
            <span className="text-white/40">ML_ENGINE</span>
            <span className="text-[#AFDDFF]">READY</span>
          </div>
          <span className="text-white/20">|</span>
          <div className="flex items-center gap-1">
            <span className="text-white/40">EVIDENCE</span>
            <span className="text-[#AFDDFF]">READY</span>
          </div>
        </div>

        {/* Dispute Search Input */}
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            placeholder="SEARCH DISPUTE (e.g. DSP_000001)..."
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            className="bg-black border border-white/20 rounded-none px-3 py-1.5 text-xs text-white placeholder-white/40 focus:outline-none focus:border-[#AFDDFF] font-mono w-64 transition-all"
          />
        </form>

        {/* Synthetic Mode Badge */}
        <div className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.03] border border-white/15 text-[#F4C46B] text-[10px] font-mono uppercase tracking-wider">
          <span>SYNTHETIC DATA MODE</span>
        </div>
      </div>
    </header>
  );
};
