import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, Database, ShieldAlert, Cpu, FileText, CheckCircle2, ArrowRight } from 'lucide-react';
import { api } from '../../services/api';
import { SimulationEvent } from '../../types';

interface LiveEventStreamProps {
  refreshIntervalMs?: number;
  onSelectCase?: (disputeId: string) => void;
}

export const LiveEventStream: React.FC<LiveEventStreamProps> = ({
  refreshIntervalMs = 2500,
  onSelectCase
}) => {
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [filterState, setFilterState] = useState<string>('ALL');
  const fetchEvents = async () => {
    try {
      const dataStateFilter = filterState === 'ALL' ? undefined : filterState;
      const list = await api.getSimulationEvents(30, dataStateFilter);
      setEvents(list);
    } catch (err) {
      console.error('Error fetching live events:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, refreshIntervalMs);
    return () => clearInterval(interval);
  }, [filterState, refreshIntervalMs]);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'TRANSACTION_RECEIVED':
        return <Radio className="w-3.5 h-3.5 text-blue-400" />;
      case 'RISK_SCORE_EVALUATED':
        return <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />;
      case 'FINANCIAL_IMPACT_CALCULATED':
        return <Cpu className="w-3.5 h-3.5 text-emerald-400" />;
      case 'CASE_CREATED':
        return <FileText className="w-3.5 h-3.5 text-indigo-400" />;
      case 'EVIDENCE_VERIFIED':
        return <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <Database className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const getDataStateBadge = (state: string) => {
    switch (state) {
      case 'SIMULATION':
        return (
          <span className="px-1.5 py-0.5 text-[9px] font-mono tracking-widest bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded uppercase">
            SIMULATION
          </span>
        );
      case 'HISTORICAL':
        return (
          <span className="px-1.5 py-0.5 text-[9px] font-mono tracking-widest bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded uppercase">
            HISTORICAL
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 text-[9px] font-mono tracking-widest bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded uppercase">
            PRODUCTION
          </span>
        );
    }
  };

  return (
    <div className="bg-[#0b0f17] border border-[#1e293b] rounded-lg p-5 shadow-2xl flex flex-col h-[450px]">
      {/* Stream Header & Filters */}
      <div className="flex items-center justify-between pb-3 border-b border-[#1e293b] shrink-0">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <h4 className="text-xs font-mono font-semibold tracking-wider text-slate-200 uppercase">
            Live Intelligence Event Stream
          </h4>
        </div>

        {/* Filter Toggle Buttons */}
        <div className="flex items-center gap-1 bg-[#070a0f] p-1 rounded border border-[#161f2e]">
          {['ALL', 'SIMULATION', 'HISTORICAL'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterState(st)}
              className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors uppercase ${
                filterState === st
                  ? 'bg-[#1e293b] text-slate-100 font-semibold'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Events List Body */}
      <div className="flex-1 overflow-y-auto mt-3 pr-1 space-y-2 font-mono text-xs custom-scrollbar">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs font-mono">
            <Database className="w-6 h-6 mb-2 text-slate-600 animate-pulse" />
            <span>AWAITING STREAM EVENTS...</span>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {events.map((evt) => (
              <motion.div
                key={evt.event_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="bg-[#0f172a]/60 hover:bg-[#0f172a] border border-[#1e293b]/70 hover:border-slate-700 rounded p-2.5 flex items-start justify-between gap-3 transition-colors group"
              >
                <div className="flex items-start gap-2.5 min-w-0">
                  <div className="p-1 bg-[#070a0f] rounded border border-slate-800 shrink-0 mt-0.5">
                    {getEventIcon(evt.event_type)}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-semibold text-slate-200 uppercase tracking-tight">
                        {evt.event_type.replace(/_/g, ' ')}
                      </span>
                      {getDataStateBadge(evt.data_state)}
                      <span className="text-[10px] text-slate-500">
                        {evt.source}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 truncate font-sans">
                      {evt.message}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col items-end shrink-0 text-right">
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                  {evt.dispute_id && onSelectCase && (
                    <button
                      onClick={() => onSelectCase(evt.dispute_id!)}
                      className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity text-[10px] text-amber-400 hover:underline flex items-center gap-0.5"
                    >
                      <span>{evt.dispute_id}</span>
                      <ArrowRight className="w-2.5 h-2.5" />
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Stream Footer Info */}
      <div className="pt-2 mt-2 border-t border-[#1e293b] flex items-center justify-between text-[10px] font-mono text-slate-500 shrink-0">
        <span>POLLING: {refreshIntervalMs}ms</span>
        <span>SHOWING {events.length} LATEST EVENTS</span>
      </div>
    </div>
  );
};
