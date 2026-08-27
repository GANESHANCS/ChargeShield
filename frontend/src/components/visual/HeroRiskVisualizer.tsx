import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export const HeroRiskVisualizer: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      const x = (e.clientX - innerWidth / 2) / (innerWidth / 2);
      const y = (e.clientY - innerHeight / 2) / (innerHeight / 2);
      setMousePos({ x, y });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <motion.div
      style={{
        transform: `perspective(1000px) rotateY(${mousePos.x * 4}deg) rotateX(${-mousePos.y * 4}deg)`
      }}
      className="relative w-full aspect-square max-w-[540px] mx-auto flex items-center justify-center transition-transform duration-300 ease-out overflow-hidden border border-white/12 bg-[#080B10]"
    >
      {/* Background Editorial Image Asset */}
      <img
        src="/assets/dashboard_risk_network.png"
        alt="Dashboard Risk Network"
        className="absolute inset-0 w-full h-full object-cover opacity-50 mix-blend-luminosity filter contrast-125 select-none"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-[#080B10] via-transparent to-[#080B10]/80" />
      {/* Outer Rotating Technical Rings */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-0 border border-white/10 rounded-full border-dashed"
      />
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-8 border border-[#AFDDFF]/20 rounded-full border-t-transparent border-b-transparent"
      />
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-20 border border-white/10 rounded-full"
      />

      {/* Central Command Core Node */}
      <div className="relative z-10 p-8 border border-[#AFDDFF]/40 bg-black/90 rounded-none shadow-[0_0_50px_rgba(175,221,255,0.15)] text-center space-y-2 backdrop-blur-md">
        <div className="flex items-center justify-center gap-2">
          <span className="h-2 w-2 bg-[#AFDDFF] animate-ping" />
          <span className="font-mono text-[10px] text-[#AFDDFF] tracking-widest uppercase">
            [ ENGINE_CORE_ACTIVE ]
          </span>
        </div>
        <div className="text-3xl font-mono font-light text-white tracking-tight">
          78.4<span className="text-[#AFDDFF]">%</span>
        </div>
        <div className="font-mono text-[10px] text-white/50 tracking-wider uppercase">
          LIGHTGBM WIN PROBABILITY
        </div>
        <div className="pt-1 flex items-center justify-center gap-1.5 font-mono text-[10px] text-[#9FE6C1]">
          <span className="h-1.5 w-1.5 bg-[#9FE6C1]" />
          <span>REC: CONTEST</span>
        </div>
      </div>

      {/* Floating Orbital Node Cards */}
      {/* 1. Transaction Stream Node */}
      <motion.div
        animate={{ y: [-6, 6, -6] }}
        transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-4 left-0 border border-white/20 bg-black/90 p-3 font-mono text-xs space-y-1 shadow-lg backdrop-blur-md max-w-[180px]"
      >
        <div className="text-white/40 text-[9px] uppercase tracking-widest">[ INCOMING_TX ]</div>
        <div className="text-white font-bold text-[11px] truncate">TX_94012849</div>
        <div className="text-[#AFDDFF] text-[10px]">₹48,500 INR</div>
      </motion.div>

      {/* 2. Feature Extraction Node */}
      <motion.div
        animate={{ y: [6, -6, 6] }}
        transition={{ duration: 5.2, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-10 right-0 border border-white/20 bg-black/90 p-3 font-mono text-xs space-y-1 shadow-lg backdrop-blur-md max-w-[180px]"
      >
        <div className="text-white/40 text-[9px] uppercase tracking-widest">[ EVIDENCE_VERIFIER ]</div>
        <div className="text-[#9FE6C1] font-bold text-[11px]">5/5 MATCHED</div>
        <div className="text-white/50 text-[10px]">CARRIER TRACKING VERIFIED</div>
      </motion.div>

      {/* 3. Human Authorization Boundary Node */}
      <motion.div
        animate={{ y: [-8, 8, -8] }}
        transition={{ duration: 4.8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute bottom-6 left-4 border border-[#AFDDFF]/30 bg-black/90 p-3 font-mono text-xs space-y-1 shadow-lg backdrop-blur-md max-w-[200px]"
      >
        <div className="text-white/40 text-[9px] uppercase tracking-widest">[ AUTHORIZATION_GATE ]</div>
        <div className="text-white font-bold text-[11px]">HUMAN AUTHORIZER</div>
        <div className="text-[#AFDDFF] text-[10px]">analyst_sarah_01</div>
      </motion.div>

      {/* 4. Financial Value Node */}
      <motion.div
        animate={{ y: [8, -8, 8] }}
        transition={{ duration: 5.8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute bottom-12 right-2 border border-white/20 bg-black/90 p-3 font-mono text-xs space-y-1 shadow-lg backdrop-blur-md max-w-[180px]"
      >
        <div className="text-white/40 text-[9px] uppercase tracking-widest">[ RECOVERY_VALUE ]</div>
        <div className="text-[#9FE6C1] font-bold text-[11px]">₹1.48M RECOVERED</div>
        <div className="text-white/50 text-[10px]">OPTIMAL 0.29 THRESHOLD</div>
      </motion.div>

      {/* Connecting Signal Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
        <line x1="20%" y1="20%" x2="50%" y2="50%" stroke="#AFDDFF" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="80%" y1="22%" x2="50%" y2="50%" stroke="#AFDDFF" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="25%" y1="80%" x2="50%" y2="50%" stroke="#9FE6C1" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="78%" y1="75%" x2="50%" y2="50%" stroke="#AFDDFF" strokeWidth="1" strokeDasharray="4 4" />
      </svg>
    </motion.div>
  );
};
