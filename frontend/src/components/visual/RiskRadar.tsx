import React from 'react';
import { motion } from 'framer-motion';

interface RiskRadarProps {
  totalCount?: number;
  highPriorityCount?: number;
  avgWinProb?: number;
}

export const RiskRadar: React.FC<RiskRadarProps> = ({
  totalCount = 120,
  highPriorityCount = 8,
  avgWinProb = 68.4
}) => {
  return (
    <div className="relative w-full aspect-video max-h-[380px] border border-white/12 bg-black/80 overflow-hidden flex items-center justify-center font-mono">
      {/* Background Radial Concentric Rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[80%] aspect-square border border-white/10 rounded-full" />
        <div className="w-[60%] aspect-square border border-[#AFDDFF]/20 rounded-full border-dashed" />
        <div className="w-[40%] aspect-square border border-white/10 rounded-full" />
        <div className="w-[20%] aspect-square border border-[#9FE6C1]/30 rounded-full" />
        {/* Crosshair Lines */}
        <div className="absolute w-full h-[1px] bg-white/10" />
        <div className="absolute h-full w-[1px] bg-white/10" />
      </div>

      {/* Rotating Radar Sweep Cone */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        className="absolute w-[80%] aspect-square rounded-full pointer-events-none"
        style={{
          background: 'conic-gradient(from 0deg, rgba(175, 221, 255, 0.25) 0deg, transparent 60deg, transparent 360deg)'
        }}
      />

      {/* Radar Blip Nodes (Active Disputes) */}
      <motion.div
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="absolute top-[28%] left-[62%] flex items-center gap-2 bg-black/90 border border-[#E68A8A] px-2.5 py-1 text-[10px] shadow-lg"
      >
        <span className="h-2 w-2 rounded-full bg-[#E68A8A] animate-ping" />
        <span className="text-[#E68A8A] font-bold">DSP_000041</span>
        <span className="text-white/60">₹18.4K (82.1%)</span>
      </motion.div>

      <motion.div
        animate={{ scale: [1, 1.15, 1] }}
        transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }}
        className="absolute bottom-[32%] left-[24%] flex items-center gap-2 bg-black/90 border border-[#F4C46B] px-2 py-1 text-[10px]"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-[#F4C46B]" />
        <span className="text-[#F4C46B]">DSP_000038</span>
      </motion.div>

      <motion.div
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 3, repeat: Infinity, delay: 1 }}
        className="absolute top-[40%] left-[35%] flex items-center gap-2 bg-black/90 border border-[#9FE6C1] px-2 py-1 text-[10px]"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-[#9FE6C1]" />
        <span className="text-[#9FE6C1]">DSP_000012</span>
      </motion.div>

      {/* Top Left Technical Radar Header */}
      <div className="absolute top-4 left-4 z-10 space-y-1">
        <div className="text-white/40 text-[9px] uppercase tracking-widest">[ RADAR_COMMAND_CENTER ]</div>
        <div className="text-white font-bold text-sm tracking-wider flex items-center gap-2 font-display">
          <span>ACTIVE RISK SCANNER</span>
          <span className="h-2 w-2 rounded-full bg-[#9FE6C1] animate-pulse" />
        </div>
      </div>

      {/* Bottom Right Live Telemetry Overlay */}
      <div className="absolute bottom-4 right-4 z-10 flex gap-4 text-[10px]">
        <div className="bg-black/90 border border-white/20 px-3 py-1.5 space-y-0.5">
          <div className="text-white/40 uppercase">SCAN VOLUME</div>
          <div className="text-white font-bold">{totalCount} DISPUTES</div>
        </div>
        <div className="bg-black/90 border border-[#E68A8A]/40 px-3 py-1.5 space-y-0.5">
          <div className="text-[#E68A8A] uppercase">HIGH RISK BLIPS</div>
          <div className="text-[#E68A8A] font-bold">{highPriorityCount} DETECTED</div>
        </div>
        <div className="bg-black/90 border border-[#AFDDFF]/40 px-3 py-1.5 space-y-0.5">
          <div className="text-[#AFDDFF] uppercase">AVG WIN PROB</div>
          <div className="text-[#AFDDFF] font-bold">{avgWinProb}%</div>
        </div>
      </div>
    </div>
  );
};
