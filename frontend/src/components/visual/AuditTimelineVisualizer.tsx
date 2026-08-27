import React from 'react';
import { motion } from 'framer-motion';
import { DecisionRecord } from '../../types';

interface AuditTimelineVisualizerProps {
  records?: DecisionRecord[];
}

export const AuditTimelineVisualizer: React.FC<AuditTimelineVisualizerProps> = ({ records = [] }) => {
  const sampleRecords = records.length > 0 ? records.slice(0, 4) : [
    { decision_id: 'DEC_000041', dispute_id: 'DSP_000041', reviewer_id: 'analyst_sarah_01', decision: 'CONTEST', ai_recommendation: 'CONTEST', ai_win_probability: 0.82, created_at: '2026-08-23T18:42:09Z' },
    { decision_id: 'DEC_000038', dispute_id: 'DSP_000038', reviewer_id: 'analyst_alex_02', decision: 'ESCALATE', ai_recommendation: 'ESCALATE', ai_win_probability: 0.48, created_at: '2026-08-23T18:41:27Z' },
    { decision_id: 'DEC_000034', dispute_id: 'DSP_000034', reviewer_id: 'analyst_sarah_01', decision: 'DO_NOT_CONTEST', ai_recommendation: 'DO_NOT_CONTEST', ai_win_probability: 0.18, created_at: '2026-08-23T18:40:11Z' }
  ];

  return (
    <div className="relative border border-white/12 bg-[#05070D] p-8 space-y-6 font-mono text-xs overflow-hidden">
      {/* Background Editorial Archive Art */}
      <img
        src="/assets/audit_institutional_archive.png"
        alt="Institutional Archive Ledger"
        className="absolute inset-0 w-full h-full object-cover opacity-25 mix-blend-luminosity filter contrast-125 select-none pointer-events-none"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[#05070D] via-[#05070D]/80 to-[#05070D]" />

      <div className="relative z-10 flex items-center justify-between border-b border-white/12 pb-4">
        <div>
          <div className="text-white/40 text-[10px] uppercase tracking-widest">[ IMMUTABLE_TIMELINE_CHAIN ]</div>
          <h3 className="text-xl font-display font-semibold text-white mt-1">Recorded Human Decision Chain</h3>
        </div>
        <span className="px-2.5 py-1 border border-[#9FE6C1]/40 text-[#9FE6C1] text-[10px] font-bold">SQLITE DB BACKED</span>
      </div>

      <div className="relative pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-[2px] before:bg-gradient-to-b before:from-[#AFDDFF] before:via-white/20 before:to-transparent">
        {sampleRecords.map((rec, idx) => {
          const isContest = rec.decision === 'CONTEST';
          const isEscalate = rec.decision === 'ESCALATE';

          return (
            <motion.div
              key={rec.decision_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: idx * 0.12 }}
              className="relative p-4 border border-white/12 bg-white/[0.01] hover:bg-white/[0.03] transition-colors space-y-2"
            >
              {/* Pulse Node Checkpoint */}
              <div className={`absolute -left-9 top-5 h-4 w-4 rounded-full border border-black flex items-center justify-center ${
                isContest ? 'bg-[#9FE6C1]' : isEscalate ? 'bg-[#F4C46B]' : 'bg-[#E68A8A]'
              }`}>
                <span className="h-1.5 w-1.5 rounded-full bg-black" />
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-2">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-[#AFDDFF] text-sm">{rec.decision_id}</span>
                  <span className="text-white font-medium">DISPUTE: {rec.dispute_id}</span>
                </div>
                <div className="text-white/40 text-[10px]">
                  {rec.created_at ? rec.created_at.replace('T', ' ').substring(0, 19) : 'N/A'}
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                <div className="text-white/70">
                  Reviewer: <span className="text-white font-bold">{rec.reviewer_id}</span>
                </div>
                <div className={`font-bold px-2 py-0.5 border text-[10px] ${
                  isContest ? 'border-[#9FE6C1] text-[#9FE6C1]' : isEscalate ? 'border-[#F4C46B] text-[#F4C46B]' : 'border-[#E68A8A] text-[#E68A8A]'
                }`}>
                  {rec.decision}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
