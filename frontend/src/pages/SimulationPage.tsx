import React from 'react';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { SectionLabel } from '../components/visual/SectionLabel';
import { EditorialImageHero } from '../components/visual/EditorialImageHero';
import { SimulationControlPanel } from '../components/simulation/SimulationControlPanel';

export const SimulationPage: React.FC = () => {
  return (
    <div className="relative min-h-screen bg-transparent">
      <AnimatedBackground variant="simulation" />

      {/* Editorial Image Hero Header */}
      <EditorialImageHero
        imageSrc="/assets/simulation_branching_paths.png"
        category="07 / BRANCHING_DECISION_TRAJECTORIES"
        titleLines={['DECISION SIMULATION', '& POLICY TESTING']}
        subtitle="Explore branching decision trajectories and test risk policy thresholds in an isolated environment without production contamination."
        metadata={[
          { label: 'ENVIRONMENT', value: 'ISOLATED SIMULATION' },
          { label: 'ISOLATION GOVERNOR', value: 'ACTIVE' },
          { label: 'PROD CONTAMINATION', value: 'STRICTLY PREVENTED' },
          { label: 'AUDIT LOGGING', value: 'ENABLED' },
        ]}
      />

      <div className="relative z-10 px-[20px] md:px-[35px] py-10 space-y-8 max-w-[1600px] mx-auto animate-lumen-fade-up">
        {/* Sub Header */}
        <div className="border-b border-white/12 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <SectionLabel label="07 / SIMULATION_CONTROL_MATRIX" badge="PHASE 9" />
            <h2 className="text-xl md:text-2xl font-display font-light text-white tracking-wide mt-1">
              CONTROLE MATRIX & SCENARIO PROFILES
            </h2>
            <p className="text-xs text-white/50 font-mono mt-1">
              Inject synthetic merchant dispute signals and observe real-time pipeline inference.
            </p>
          </div>
          <div className="flex items-center gap-2 border border-[#E879F9]/30 bg-[#E879F9]/10 text-[#E879F9] px-3 py-1.5 font-mono text-xs uppercase tracking-widest">
            <span className="h-2 w-2 rounded-full bg-[#E879F9] animate-pulse" />
            <span>[ SIMULATION GOVERNOR ACTIVE ]</span>
          </div>
        </div>

        {/* Control Panel */}
        <SimulationControlPanel />
      </div>
    </div>
  );
};
