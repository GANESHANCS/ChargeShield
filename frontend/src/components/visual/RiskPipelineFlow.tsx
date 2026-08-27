import React from 'react';
import { motion } from 'framer-motion';

export const RiskPipelineFlow: React.FC = () => {
  const steps = [
    {
      label: '01 // DISPUTE INGESTION',
      title: 'TRANSACTION DATA',
      sub: 'Relational features & order metadata ingested',
      badge: 'PHASE_01',
      color: 'white'
    },
    {
      label: '02 // FEATURE ENGINE',
      title: 'FEATURE EXTRACTION',
      sub: 'Auth risk, carrier tracking & customer history',
      badge: 'PHASE_02',
      color: 'ice'
    },
    {
      label: '03 // ML TRIAGE',
      title: 'LIGHTGBM CLASSIFIER',
      sub: 'Cost-sensitive threshold evaluation @ 0.29',
      badge: 'PHASE_02',
      color: 'ice'
    },
    {
      label: '04 // PROBABILITY',
      title: 'WIN PROBABILITY',
      sub: 'Calculates expected financial recovery likelihood',
      badge: 'PHASE_04',
      color: 'green'
    },
    {
      label: '05 // AUTHORIZATION',
      title: 'HUMAN AUTHORIZER',
      sub: 'Immutable decision recording into SQLite DB',
      badge: 'PHASE_06',
      color: 'green'
    }
  ];

  return (
    <div className="relative w-full space-y-4 font-mono text-xs">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {steps.map((step, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: idx * 0.12 }}
            className={`p-4 border bg-black/90 space-y-3 relative ${
              step.color === 'ice'
                ? 'border-[#AFDDFF]/40 text-[#AFDDFF]'
                : step.color === 'green'
                ? 'border-[#9FE6C1]/40 text-[#9FE6C1]'
                : 'border-white/20 text-white'
            }`}
          >
            <div className="flex items-center justify-between text-[9px] text-white/40 uppercase tracking-widest">
              <span>{step.label}</span>
              <span className="px-1 border border-white/20 text-white">{step.badge}</span>
            </div>

            <div className="font-bold text-sm text-white tracking-wider font-display">
              {step.title}
            </div>

            <p className="text-[11px] text-white/50 leading-relaxed font-sans">
              {step.sub}
            </p>

            {/* Connecting Directional Arrow indicator for desktop */}
            {idx < steps.length - 1 && (
              <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-20 text-[#AFDDFF] font-bold text-xs bg-black px-0.5">
                &rarr;
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};
