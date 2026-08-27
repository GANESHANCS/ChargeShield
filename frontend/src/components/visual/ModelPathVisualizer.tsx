import React, { useState } from 'react';
import { motion } from 'framer-motion';

export const ModelPathVisualizer: React.FC = () => {
  const [threshold, setThreshold] = useState<number>(0.29);

  // Dynamic calculations based on decision threshold slider
  const accuracy = (0.74 + (0.15 * Math.abs(0.29 - threshold))).toFixed(2);
  const costSavings = Math.round(148500 * (1 - Math.pow(threshold - 0.29, 2) * 4));
  const recallPct = Math.round(Math.min(98, Math.max(45, 92 - (threshold - 0.29) * 80)));
  const precisionPct = Math.round(Math.min(95, Math.max(50, 68 + (threshold - 0.29) * 70)));

  return (
    <div className="relative border border-white/12 bg-[#070612] p-8 space-y-8 font-mono text-xs overflow-hidden">
      {/* Background Editorial Mathematical Boundary Art */}
      <img
        src="/assets/model_math_boundary.png"
        alt="Mathematical Decision Boundary"
        className="absolute inset-0 w-full h-full object-cover opacity-30 mix-blend-luminosity filter contrast-125 select-none pointer-events-none"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[#070612] via-[#070612]/80 to-[#070612]" />

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/12 pb-4">
        <div>
          <div className="text-white/40 text-[10px] uppercase tracking-widest">[ AI_LABORATORY_EXPERIMENT ]</div>
          <h3 className="text-xl font-display font-semibold text-white mt-1">Dual Algorithm Classification Paths</h3>
        </div>
        
        {/* Interactive Threshold Control */}
        <div className="p-3 border border-[#AFDDFF]/40 bg-black/80 flex items-center gap-4">
          <div className="space-y-0.5">
            <div className="text-[9px] text-white/40 uppercase">DECISION THRESHOLD</div>
            <div className="text-sm font-bold text-[#AFDDFF]">{threshold.toFixed(2)}</div>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.80"
            step="0.01"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-32 accent-[#AFDDFF] cursor-pointer"
          />
          <button
            onClick={() => setThreshold(0.29)}
            className="text-[9px] px-2 py-1 border border-[#AFDDFF]/30 text-[#AFDDFF] hover:bg-[#AFDDFF]/20 uppercase"
          >
            [ OPTIMAL: 0.29 ]
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center relative">
        {/* Primary Path: LightGBM */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="border border-[#AFDDFF]/40 bg-white/[0.01] p-6 space-y-4 relative"
        >
          <div className="flex items-center justify-between border-b border-white/12 pb-3">
            <span className="text-[#AFDDFF] font-bold text-sm font-display">PRIMARY: LIGHTGBM CLASSIFIER</span>
            <span className="text-[#9FE6C1] font-bold text-[10px]">SELECTED PRIMARY</span>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-white/60 text-[11px]">
              <span>ACCURACY (THRESHOLD: {threshold.toFixed(2)})</span>
              <span className="text-white font-bold">{accuracy}</span>
            </div>
            <div className="w-full bg-white/10 h-2">
              <motion.div initial={{ width: 0 }} animate={{ width: `${parseFloat(accuracy) * 100}%` }} transition={{ duration: 0.5 }} className="bg-[#AFDDFF] h-full" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-white/60 text-[11px]">
              <span>COST REDUCTION SAVINGS</span>
              <span className="text-[#9FE6C1] font-bold">₹{costSavings.toLocaleString('en-IN')} INR</span>
            </div>
            <div className="w-full bg-white/10 h-2">
              <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, Math.max(10, (costSavings / 150000) * 100))}%` }} transition={{ duration: 0.5 }} className="bg-[#9FE6C1] h-full" />
            </div>
          </div>

          <div className="flex justify-between text-[10px] text-white/40 pt-1">
            <span>RECALL: {recallPct}%</span>
            <span>PRECISION: {precisionPct}%</span>
          </div>
        </motion.div>

        {/* Baseline Path: Logistic Regression */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="border border-white/20 bg-white/[0.01] p-6 space-y-4 relative"
        >
          <div className="flex items-center justify-between border-b border-white/12 pb-3">
            <span className="text-white/80 font-bold text-sm font-display">BASELINE: LOGISTIC REGRESSION</span>
            <span className="text-white/40 text-[10px]">BENCHMARK</span>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-white/60 text-[11px]">
              <span>ROC-AUC SCORE</span>
              <span className="text-white/80 font-bold">0.7104</span>
            </div>
            <div className="w-full bg-white/10 h-2">
              <motion.div initial={{ width: 0 }} animate={{ width: '71.04%' }} transition={{ duration: 1 }} className="bg-white/40 h-full" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-white/60 text-[11px]">
              <span>NET FINANCIAL LOSS</span>
              <span className="text-[#E68A8A] font-bold">₹284,000 INR</span>
            </div>
            <div className="w-full bg-white/10 h-2">
              <motion.div initial={{ width: 0 }} animate={{ width: '54%' }} transition={{ duration: 1.2 }} className="bg-[#E68A8A] h-full" />
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
