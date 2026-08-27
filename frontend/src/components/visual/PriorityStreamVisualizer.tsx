import React from 'react';
import { motion } from 'framer-motion';
import { ReviewQueueItem } from '../../types';

interface PriorityStreamVisualizerProps {
  items?: ReviewQueueItem[];
}

export const PriorityStreamVisualizer: React.FC<PriorityStreamVisualizerProps> = ({ items = [] }) => {
  const displayItems = items.length > 0 ? items.slice(0, 4) : [
    { dispute_id: 'DSP_000041', disputed_amount: 18400, priority_score: 82.1, win_probability: 0.82, ai_recommendation: 'CONTEST' },
    { dispute_id: 'DSP_000038', disputed_amount: 12900, priority_score: 71.4, win_probability: 0.71, ai_recommendation: 'CONTEST' },
    { dispute_id: 'DSP_000032', disputed_amount: 7800, priority_score: 63.2, win_probability: 0.63, ai_recommendation: 'DO_NOT_CONTEST' },
    { dispute_id: 'DSP_000029', disputed_amount: 24500, priority_score: 48.0, win_probability: 0.48, ai_recommendation: 'ESCALATE' }
  ];

  return (
    <div className="relative border border-white/12 bg-[#080B10] p-6 space-y-4 font-mono text-xs overflow-hidden">
      {/* Background Stream Artwork */}
      <img
        src="/assets/queue_transaction_stream.png"
        alt="Transaction Stream"
        className="absolute inset-0 w-full h-full object-cover opacity-20 mix-blend-luminosity filter contrast-125 select-none pointer-events-none"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[#080B10] via-transparent to-[#080B10]" />

      <div className="relative z-10 flex items-center justify-between border-b border-white/12 pb-3">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-[#AFDDFF] animate-ping" />
          <span className="text-white font-bold tracking-wider font-display text-sm">
            LIVE RISK PRIORITY STREAM
          </span>
        </div>
        <span className="text-white/40 text-[10px] uppercase tracking-widest">[ REAL-TIME TRIAGE ]</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {displayItems.map((item, idx) => {
          const isHigh = item.win_probability >= 0.6;
          const isMedium = item.win_probability >= 0.29 && item.win_probability < 0.6;

          return (
            <motion.div
              key={item.dispute_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              className={`p-4 border bg-white/[0.01] hover:bg-white/[0.04] transition-all space-y-2 relative group ${
                isHigh
                  ? 'border-[#AFDDFF]/40 hover:border-[#AFDDFF]'
                  : isMedium
                  ? 'border-[#F4C46B]/40 hover:border-[#F4C46B]'
                  : 'border-[#E68A8A]/40 hover:border-[#E68A8A]'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] text-white/40">
                <span>PRIORITY STREAM #{idx + 1}</span>
                <span className={`font-bold ${isHigh ? 'text-[#AFDDFF]' : isMedium ? 'text-[#F4C46B]' : 'text-[#E68A8A]'}`}>
                  {(item.win_probability * 100).toFixed(1)}% WIN PROB
                </span>
              </div>

              <div className="text-white font-bold text-sm tracking-wider font-mono">
                {item.dispute_id}
              </div>

              <div className="flex items-center justify-between text-[11px] pt-1">
                <span className="text-white/70">₹{item.disputed_amount.toLocaleString('en-IN')}</span>
                <span className="px-2 py-0.5 border border-white/20 text-white text-[10px]">
                  {item.ai_recommendation}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
