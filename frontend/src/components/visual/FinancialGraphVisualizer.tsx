import React from 'react';
import { motion } from 'framer-motion';

interface FinancialGraphVisualizerProps {
  totalDisputes?: number;
  simulatedSavings?: number;
}

export const FinancialGraphVisualizer: React.FC<FinancialGraphVisualizerProps> = ({
  totalDisputes = 120,
  simulatedSavings = 148500
}) => {
  return (
    <div className="border border-[#AFDDFF]/40 bg-[#101722] p-8 space-y-6 font-mono text-xs shadow-[0_0_50px_rgba(175,221,255,0.08)] relative overflow-hidden">
      {/* Background Editorial Landscape Art */}
      <img
        src="/assets/analytics_financial_landscape.png"
        alt="Financial Data Landscape"
        className="absolute inset-0 w-full h-full object-cover opacity-25 mix-blend-luminosity filter contrast-125 select-none pointer-events-none"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[#101722] via-[#101722]/80 to-[#101722]" />
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4 relative z-10">
        <div>
          <div className="text-[#9D8CFF] text-[10px] uppercase tracking-widest">[ EXECUTIVE_FINANCIAL_INTELLIGENCE ]</div>
          <h3 className="text-2xl font-display font-bold text-white mt-1">Financial Recovery Performance</h3>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 border border-[#76E0C2]/40 bg-[#76E0C2]/10 text-[#76E0C2] font-bold text-xs">
          <span className="h-2 w-2 rounded-full bg-[#76E0C2] animate-pulse" />
          <span>REAL-TIME CALCULATED</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 relative z-10">
        <div className="p-4 border border-white/12 bg-black/80 space-y-2">
          <div className="text-white/40 text-[10px]">TOTAL DISPUTES INGESTED</div>
          <div className="text-3xl font-bold text-white">{totalDisputes}</div>
          <div className="text-[10px] text-white/50">Synthetic relational corpus</div>
        </div>

        <div className="p-4 border border-[#76E0C2]/40 bg-black/80 space-y-2">
          <div className="text-[#76E0C2] text-[10px] font-bold">OPTIMAL RECOVERABLE SAVINGS</div>
          <div className="text-3xl font-bold text-[#76E0C2]">₹{simulatedSavings.toLocaleString('en-IN')} INR</div>
          <div className="text-[10px] text-[#76E0C2]/80">Over naive contestation strategy</div>
        </div>

        <div className="p-4 border border-[#9D8CFF]/40 bg-black/80 space-y-2">
          <div className="text-[#9D8CFF] text-[10px] font-bold">AI / HUMAN ALIGNMENT RATE</div>
          <div className="text-3xl font-bold text-[#9D8CFF]">88.5%</div>
          <div className="text-[10px] text-[#9D8CFF]/80">Decision agreement score</div>
        </div>
      </div>

      {/* Trajectory Financial Graph Illustration */}
      <div className="relative h-24 w-full pt-4">
        <svg className="w-full h-full">
          <motion.path
            d="M 0 80 Q 200 20, 400 60 T 800 10 T 1200 30"
            fill="none"
            stroke="#76E0C2"
            strokeWidth="3"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 2, ease: 'easeInOut' }}
          />
          <motion.path
            d="M 0 85 Q 200 35, 400 70 T 800 25 T 1200 45"
            fill="none"
            stroke="#9D8CFF"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            transition={{ duration: 1, delay: 1 }}
          />
        </svg>
      </div>
    </div>
  );
};
