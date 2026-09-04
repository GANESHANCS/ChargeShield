import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { ThinDivider } from '../components/visual/ThinDivider';

export const IntroPage: React.FC = () => {
  const navigate = useNavigate();

  const handleEnter = () => {
    navigate('/login');
  };

  const capabilityAreas = [
    {
      title: 'RISK INTELLIGENCE',
      description: 'Identify and prioritize chargeback exposure.',
      code: '01'
    },
    {
      title: 'CASE INVESTIGATION',
      description: 'Trace transactions, customers, disputes and risk signals.',
      code: '02'
    },
    {
      title: 'EVIDENCE & REPRESENTMENT',
      description: 'Organize evidence and generate an audit-ready representment package.',
      code: '03'
    },
    {
      title: 'OUTCOMES & LEARNING',
      description: 'Track outcomes and evaluate model performance without autonomous retraining.',
      code: '04'
    }
  ];

  return (
    <div className="min-h-screen w-full bg-[#05070D] text-white font-sans overflow-x-hidden relative flex flex-col justify-between select-none">
      {/* 1. Cinematic Background Architecture */}
      <AnimatedBackground variant="intro" />

      {/* Subtle Structural Grid & Ambient Overlay */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:5rem_5rem] pointer-events-none z-0 opacity-40" />

      {/* 2. Top Minimal Institutional Header */}
      <header className="relative z-10 w-full max-w-[1440px] mx-auto px-6 md:px-12 pt-8 pb-4 flex items-center justify-between font-mono text-xs border-b border-white/10">
        <div className="flex items-center gap-3">
          <span className="h-1.5 w-1.5 bg-[#AFDDFF] rounded-full animate-pulse" />
          <span className="font-display font-medium text-sm tracking-widest text-white">CHARGESHIELD</span>
        </div>
        <div className="text-[10px] md:text-xs text-white/50 tracking-widest uppercase border border-white/12 px-3 py-1.5 bg-black/40 backdrop-blur-md">
          PLATFORM INTRODUCTION
        </div>
      </header>

      {/* 3. Main Hero & Capability Composition */}
      <main className="relative z-10 my-auto w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 md:py-16 flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-4xl w-full space-y-8"
        >
          {/* Primary Branding */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1 border border-[#AFDDFF]/30 bg-[#AFDDFF]/5 font-mono text-[11px] text-[#AFDDFF] tracking-widest uppercase">
            <span>CHARGESHIELD</span>
          </div>

          {/* Primary Headline */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-display font-light tracking-tight text-white leading-[1.05]">
            CHARGEBACK DEFENSE<br />
            <span className="font-semibold text-white tracking-tight">INTELLIGENCE</span>
          </h1>

          {/* Supporting Copy */}
          <p className="text-sm md:text-base font-mono text-white/70 max-w-2xl mx-auto leading-relaxed font-normal">
            Investigate disputes. Quantify exposure.
            <br className="hidden sm:inline" />
            Assemble evidence. Make defensible decisions.
          </p>

          {/* Divider */}
          <div className="py-4">
            <ThinDivider />
          </div>

          {/* Capability Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 text-left">
            {capabilityAreas.map((cap) => (
              <motion.div
                key={cap.code}
                whileHover={{ y: -2 }}
                className="p-5 md:p-6 border border-white/12 bg-black/60 backdrop-blur-md space-y-3 relative group transition-colors hover:border-[#AFDDFF]/40"
              >
                <div className="flex items-center justify-between font-mono text-[10px] text-white/40 border-b border-white/10 pb-2">
                  <span>CAPABILITY // {cap.code}</span>
                  <span className="text-[#AFDDFF] opacity-0 group-hover:opacity-100 transition-opacity">&bull;</span>
                </div>
                <h2 className="font-display text-sm md:text-base font-medium text-white tracking-wide group-hover:text-[#AFDDFF] transition-colors">
                  {cap.title}
                </h2>
                <p className="font-mono text-xs text-white/60 leading-normal">
                  {cap.description}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Primary Action CTA */}
          <div className="pt-8 md:pt-10 flex flex-col items-center gap-4">
            <button
              onClick={handleEnter}
              aria-label="Enter ChargeShield risk operations platform"
              className="group relative inline-flex items-center justify-center px-8 py-4 bg-white text-black font-mono text-xs md:text-sm font-bold tracking-widest uppercase transition-all duration-300 hover:bg-[#AFDDFF] focus:outline-none focus:ring-2 focus:ring-[#AFDDFF] focus:ring-offset-2 focus:ring-offset-[#05070D] shadow-[0_0_30px_rgba(255,255,255,0.15)] hover:shadow-[0_0_40px_rgba(175,221,255,0.35)] cursor-pointer"
            >
              <span>ENTER CHARGESHIELD &rarr;</span>
            </button>

            {/* Subtle Secondary Status / Metadata Treatment */}
            <div className="font-mono text-[10px] md:text-[11px] text-white/40 tracking-widest uppercase flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 pt-2">
              <span>DECISION INTELLIGENCE PLATFORM</span>
              <span className="hidden sm:inline text-white/20">//</span>
              <span>DISPUTE OPERATIONS / RISK / EVIDENCE</span>
            </div>
          </div>
        </motion.div>
      </main>

      {/* 4. Minimal Institutional Footer */}
      <footer className="relative z-10 w-full max-w-[1440px] mx-auto px-6 md:px-12 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-white/10 font-mono text-[10px] text-white/40">
        <div>CHARGESHIELD // ENTERPRISE DISPUTE INTELLIGENCE SYSTEM</div>
        <div>INSTITUTIONAL AUTHORIZATION BOUNDARY</div>
      </footer>
    </div>
  );
};

export default IntroPage;
