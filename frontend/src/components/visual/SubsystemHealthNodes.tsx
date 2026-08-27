import React from 'react';
import { motion } from 'framer-motion';

interface SubsystemHealthNodesProps {
  healthData?: {
    api?: string;
    database?: string;
    ml_engine?: string;
    evidence_engine?: string;
    review_engine?: string;
  };
}

export const SubsystemHealthNodes: React.FC<SubsystemHealthNodesProps> = ({ healthData }) => {
  const subsystems = [
    { label: 'FASTAPI REST SERVER', key: 'api', defaultStatus: 'CONNECTED' },
    { label: 'SQLITE DATABASE (chargeshield.db)', key: 'database', defaultStatus: 'HEALTHY' },
    { label: 'LIGHTGBM ML ENGINE', key: 'ml_engine', defaultStatus: 'READY' },
    { label: 'PHASE 5 EVIDENCE VERIFIER', key: 'evidence_engine', defaultStatus: 'VERIFIED' },
    { label: 'PHASE 6 PERSISTENT AUDIT STORE', key: 'review_engine', defaultStatus: 'ACTIVE' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 font-mono text-xs">
      {subsystems.map((sub, idx) => {
        const rawStatus = (healthData as any)?.[sub.key] || sub.defaultStatus;
        const isHealthy = rawStatus === 'HEALTHY' || rawStatus === 'READY' || rawStatus === 'CONNECTED' || rawStatus === 'VERIFIED' || rawStatus === 'ACTIVE';

        return (
          <motion.div
            key={idx}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: idx * 0.1 }}
            className="p-4 border border-white/12 bg-black space-y-3 relative overflow-hidden"
          >
            <div className="text-white/40 text-[9px] uppercase tracking-widest">[ SYSTEM_NODE ]</div>
            <div className="text-white font-medium text-[11px] truncate">{sub.label}</div>

            <div className="flex items-center justify-between pt-1">
              <span className={`text-[10px] font-bold uppercase tracking-wider ${isHealthy ? 'text-[#9FE6C1]' : 'text-[#E68A8A]'}`}>
                {rawStatus}
              </span>
              <div className="relative flex items-center justify-center h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isHealthy ? 'bg-[#9FE6C1]' : 'bg-[#E68A8A]'}`} />
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isHealthy ? 'bg-[#9FE6C1]' : 'bg-[#E68A8A]'}`} />
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
