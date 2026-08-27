import React from 'react';
import { motion } from 'framer-motion';

interface EvidenceNetworkVisualizerProps {
  disputeId?: string;
  winProb?: number;
  recommendation?: string;
}

export const EvidenceNetworkVisualizer: React.FC<EvidenceNetworkVisualizerProps> = ({
  disputeId = 'DSP_000001',
  winProb = 78.4,
  recommendation = 'CONTEST'
}) => {
  const nodes = [
    { title: 'BILLING_MATCH', sub: 'Address & Postal Verified', verified: true, pos: 'top-2 left-6' },
    { title: 'DEVICE_FINGERPRINT', sub: '12 Repeat Order Logs', verified: true, pos: 'top-2 right-6' },
    { title: 'CARRIER_TRACKING', sub: 'Signed at Recipient', verified: true, pos: 'bottom-2 left-6' },
    { title: 'CUSTOMER_HISTORY', sub: '420 Days Account Tenure', verified: true, pos: 'bottom-2 right-6' }
  ];

  return (
    <div className="relative w-full aspect-video max-h-[420px] border border-white/12 bg-[#0B1017] p-6 flex items-center justify-center font-mono overflow-hidden">
      {/* Background Editorial Evidence Art */}
      <img
        src="/assets/case_investigative_evidence.png"
        alt="Investigative Evidence"
        className="absolute inset-0 w-full h-full object-cover opacity-35 mix-blend-luminosity filter contrast-125 select-none pointer-events-none"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1017] via-transparent to-[#0B1017]/80" />
      {/* Central Case Node */}
      <motion.div
        animate={{ scale: [1, 1.03, 1] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        className="relative z-20 p-6 border border-[#AFDDFF]/50 bg-black/95 text-center shadow-[0_0_40px_rgba(175,221,255,0.2)] space-y-2 min-w-[220px]"
      >
        <div className="text-white/40 text-[9px] uppercase tracking-widest">[ CENTRAL_DISPUTE_NODE ]</div>
        <div className="text-2xl font-bold text-white font-display">
          CASE <span className="text-[#AFDDFF]">//</span> {disputeId}
        </div>
        <div className="text-xl font-bold text-[#AFDDFF]">{winProb}% WIN PROB</div>
        <div className="text-xs text-[#9FE6C1] font-bold">REC: {recommendation}</div>
      </motion.div>

      {/* Orbital Evidence Nodes */}
      {nodes.map((node, idx) => (
        <motion.div
          key={node.title}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: idx * 0.15 }}
          className={`absolute ${node.pos} z-20 p-4 border bg-black/90 space-y-1 max-w-[200px] shadow-lg ${
            node.verified ? 'border-[#9FE6C1]/40' : 'border-white/20'
          }`}
        >
          <div className="text-[#AFDDFF] text-[10px] font-bold">[{node.title}]</div>
          <div className="text-white font-medium text-xs truncate">{node.sub}</div>
          <div className="text-[#9FE6C1] font-bold text-[9px] pt-1">100% VERIFIED</div>
        </motion.div>
      ))}

      {/* Connecting Laser Beams */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-10 opacity-50">
        <line x1="20%" y1="20%" x2="50%" y2="50%" stroke="#AFDDFF" strokeWidth="1.5" strokeDasharray="4 4" />
        <line x1="80%" y1="20%" x2="50%" y2="50%" stroke="#AFDDFF" strokeWidth="1.5" strokeDasharray="4 4" />
        <line x1="20%" y1="80%" x2="50%" y2="50%" stroke="#9FE6C1" strokeWidth="1.5" strokeDasharray="4 4" />
        <line x1="80%" y1="80%" x2="50%" y2="50%" stroke="#9FE6C1" strokeWidth="1.5" strokeDasharray="4 4" />
      </svg>
    </div>
  );
};
