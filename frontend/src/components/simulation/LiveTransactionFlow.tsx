import React from 'react';
import { motion } from 'framer-motion';
import { Radio, ShieldAlert, DollarSign, FileText, CheckCircle2 } from 'lucide-react';
import { GeneratedSimTransaction } from '../../types';

interface LiveTransactionFlowProps {
  latestTransaction?: GeneratedSimTransaction | null;
}

export const LiveTransactionFlow: React.FC<LiveTransactionFlowProps> = ({ latestTransaction }) => {
  const stages = [
    {
      id: 'ingest',
      label: '1. INGESTION',
      subtext: 'Transaction Stream',
      icon: Radio,
      active: true,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10 border-blue-500/30'
    },
    {
      id: 'ml_triage',
      label: '2. ML TRIAGE',
      subtext: latestTransaction ? `Win Prob: ${(latestTransaction.win_probability * 100).toFixed(0)}%` : 'LightGBM Scoring',
      icon: ShieldAlert,
      active: !!latestTransaction,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10 border-amber-500/30'
    },
    {
      id: 'financial',
      label: '3. FINANCIAL IMPACT',
      subtext: latestTransaction ? `₹${latestTransaction.disputed_amount.toLocaleString()}` : 'Fee & Net Value',
      icon: DollarSign,
      active: !!latestTransaction,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10 border-emerald-500/30'
    },
    {
      id: 'case',
      label: '4. CASE ENGINE',
      subtext: latestTransaction ? `${latestTransaction.priority} TIER` : 'Priority Classification',
      icon: FileText,
      active: !!latestTransaction,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10 border-indigo-500/30'
    },
    {
      id: 'evidence',
      label: '5. EVIDENCE NETWORK',
      subtext: latestTransaction ? `Rec: ${latestTransaction.recommendation}` : 'SHAP & Grounding',
      icon: CheckCircle2,
      active: !!latestTransaction,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10 border-purple-500/30'
    }
  ];

  return (
    <div className="bg-[#0b0f17] border border-[#1e293b] rounded-lg p-5 shadow-2xl overflow-hidden relative">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#1e293b]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          <h4 className="text-xs font-mono font-semibold tracking-wider text-slate-200 uppercase">
            Real-Time Pipeline Flow Node
          </h4>
        </div>
        {latestTransaction && (
          <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 uppercase tracking-widest">
            ACTIVE CASE: {latestTransaction.dispute_id}
          </span>
        )}
      </div>

      {/* Stage Nodes Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-5 gap-3 relative">
        {stages.map((stage, idx) => {
          const IconComponent = stage.icon;
          return (
            <motion.div
              key={stage.id}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: idx * 0.1 }}
              className={`p-3 rounded-md border flex flex-col justify-between transition-all duration-300 ${
                stage.active
                  ? `${stage.bgColor} shadow-lg`
                  : 'bg-[#070a0f] border-[#161f2e] opacity-60'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <IconComponent className={`w-4 h-4 ${stage.color}`} />
                  <span className="text-[9px] font-mono text-slate-500 uppercase">NODE 0{idx + 1}</span>
                </div>
                <div className="text-[11px] font-mono font-semibold text-slate-200 uppercase tracking-wider">
                  {stage.label}
                </div>
                <div className="text-[10px] text-slate-400 mt-1 font-sans">
                  {stage.subtext}
                </div>
              </div>

              {stage.active && (
                <div className="mt-3 pt-2 border-t border-slate-700/30 flex items-center justify-between text-[9px] font-mono text-slate-400">
                  <span>STATUS</span>
                  <span className="text-emerald-400 uppercase font-bold">PROCESSED</span>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
