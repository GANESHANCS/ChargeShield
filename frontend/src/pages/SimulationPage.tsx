import React from 'react';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { SectionLabel } from '../components/visual/SectionLabel';
import { SimulationControlPanel } from '../components/simulation/SimulationControlPanel';

export const SimulationPage: React.FC = () => {
  return (
    <div className="relative min-h-screen bg-transparent">
      <AnimatedBackground variant="simulation" />

      <div className="relative z-10 px-[20px] md:px-[35px] py-10 space-y-8 max-w-[1600px] mx-auto animate-lumen-fade-up">
        {/* Header */}
        <div className="border-b border-white/12 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <SectionLabel label="07 / DECISION_SIMULATION" />
            <h1 className="text-2xl md:text-3xl font-display font-light text-white tracking-wide mt-1">
              DECISION SIMULATION ENGINE
            </h1>
            <p className="text-xs text-white/50 font-mono mt-1">
              Explore branching decision trajectories and test risk policy thresholds in an isolated environment.
            </p>
          </div>
          <div className="flex items-center gap-2 border border-[#AFDDFF]/30 bg-[#AFDDFF]/10 text-[#AFDDFF] px-3 py-1.5 font-mono text-xs uppercase tracking-widest">
            <span className="h-2 w-2 rounded-full bg-[#AFDDFF] animate-pulse" />
            <span>[ SIMULATION ENVIRONMENT ]</span>
          </div>
        </div>

        {/* Control Panel */}
        <SimulationControlPanel />
      </div>
    </div>
  );
};
