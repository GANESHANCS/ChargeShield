import React, { useState, useEffect } from 'react';
import { Play, Square, Zap, RefreshCw, Layers, Activity, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { SimulationStatus, SimulationScenarioDetail, GeneratedSimTransaction } from '../../types';

interface SimulationControlPanelProps {
  onEventGenerated?: (txn?: GeneratedSimTransaction) => void;
  onStateChange?: (status: SimulationStatus) => void;
}

export const SimulationControlPanel: React.FC<SimulationControlPanelProps> = ({
  onEventGenerated,
  onStateChange
}) => {
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [scenarios, setScenarios] = useState<SimulationScenarioDetail[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('HIGH_RISK_CHARGEBACK');
  const [loading, setLoading] = useState<boolean>(false);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const st = await api.getSimulationStatus();
      setStatus(st);
      if (onStateChange) onStateChange(st);
    } catch (err: any) {
      console.error('Failed to fetch simulation status:', err);
    }
  };

  const fetchScenarios = async () => {
    try {
      const list = await api.getSimulationScenarios();
      setScenarios(list);
    } catch (err: any) {
      console.error('Failed to fetch simulation scenarios:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchScenarios();

    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      if (status?.running) {
        const res = await api.stopSimulation();
        setStatus(res);
        if (onStateChange) onStateChange(res);
      } else {
        const res = await api.startSimulation(selectedScenario);
        setStatus(res);
        if (onStateChange) onStateChange(res);
      }
    } catch (err: any) {
      setError(err.message || 'Simulation state transition failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleInjectSingleTransaction = async () => {
    setTriggering(true);
    setError(null);
    try {
      const res = await api.generateSimulationTransaction(selectedScenario);
      await fetchStatus();
      if (onEventGenerated) onEventGenerated(res);
    } catch (err: any) {
      setError(err.message || 'Failed to inject simulation transaction.');
    } finally {
      setTriggering(false);
    }
  };

  const isRunning = status?.running || false;

  return (
    <div className="bg-[#0b0f17] border border-[#1e293b] rounded-lg p-5 shadow-2xl relative overflow-hidden">
      {/* Background Subtle Tech Watermark */}
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none font-mono text-xs tracking-widest text-slate-400 select-none">
        ENGINE // SIMULATION_v9.0
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2">
            <Activity className={`w-4 h-4 ${isRunning ? 'text-amber-400 animate-pulse' : 'text-slate-400'}`} />
            <h3 className="text-sm font-semibold tracking-wider uppercase text-slate-100 font-mono">
              Real-Time Simulation Engine
            </h3>
            <span className={`px-2 py-0.5 text-[10px] font-mono tracking-widest rounded uppercase ${
              isRunning 
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' 
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}>
              {isRunning ? '● SIMULATION ACTIVE' : '○ STANDBY'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-serif italic">
            Inject deterministic fraud vectors into the intelligence pipeline without altering production audit records.
          </p>
        </div>

        {/* Counter Badges */}
        <div className="flex items-center gap-3 bg-[#0f172a] border border-[#1e293b] rounded-md px-3 py-1.5 font-mono text-xs">
          <div>
            <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Events</span>
            <span className="text-slate-200 font-bold">{status?.events_processed || 0}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div>
            <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Transactions</span>
            <span className="text-slate-200 font-bold">{status?.transactions_processed || 0}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div>
            <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Cases</span>
            <span className="text-amber-400 font-bold">{status?.cases_created || 0}</span>
          </div>
        </div>
      </div>

      {/* Control Strip */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
        {/* Scenario Selector */}
        <div className="md:col-span-6 flex flex-col gap-1">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Layers className="w-3 h-3 text-slate-500" /> Scenario Profile
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            disabled={isRunning}
            className="bg-[#0f172a] border border-[#1e293b] text-slate-200 text-xs rounded px-3 py-2 focus:outline-none focus:border-amber-500/50 disabled:opacity-50 font-mono transition-colors"
          >
            {scenarios.map((sc) => (
              <option key={sc.scenario_id} value={sc.scenario_id}>
                {sc.name} ({sc.target_risk_tier} Risk — {sc.target_recommendation})
              </option>
            ))}
          </select>
        </div>

        {/* Action Controls */}
        <div className="md:col-span-6 flex items-center gap-2 mt-2 md:mt-4">
          <button
            onClick={handleToggleSimulation}
            disabled={loading}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 text-xs font-mono tracking-wider rounded transition-all duration-200 uppercase font-semibold ${
              isRunning
                ? 'bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
                : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
            }`}
          >
            {isRunning ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" /> Stop Simulation
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" /> Start Live Stream
              </>
            )}
          </button>

          <button
            onClick={handleInjectSingleTransaction}
            disabled={triggering || isRunning}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono tracking-wider rounded transition-all duration-200 uppercase disabled:opacity-40"
            title="Inject single transaction event immediately"
          >
            <Zap className={`w-3.5 h-3.5 ${triggering ? 'animate-bounce text-amber-400' : 'text-slate-400'}`} />
            <span>Inject Event</span>
          </button>

          <button
            onClick={fetchStatus}
            className="p-2 bg-[#0f172a] hover:bg-slate-800 text-slate-400 border border-[#1e293b] rounded transition-colors"
            title="Refresh Status"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Selected Scenario Description Strip */}
      {selectedScenario && (
        <div className="mt-3 text-[11px] font-sans text-slate-400 bg-[#070a0f] border border-[#161f2e] rounded px-3 py-2 flex items-center justify-between">
          <span className="text-slate-300">
            {scenarios.find((s) => s.scenario_id === selectedScenario)?.description || 'Deterministic transaction scenario profile.'}
          </span>
          <span className="font-mono text-[10px] text-amber-400/80 uppercase tracking-widest ml-2 whitespace-nowrap">
            Isolated [SIMULATION] state
          </span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-3 flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2 rounded">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
