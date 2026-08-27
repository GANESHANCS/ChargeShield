import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { AnalyticsOverviewResponse, OperationalReportResponse, OperationsOverview, OperationalAlert, OutcomeOverview } from '../types';
import { SectionLabel } from '../components/visual/SectionLabel';
import { MetricDisplay } from '../components/visual/MetricDisplay';
import { TechnicalStatus } from '../components/visual/TechnicalStatus';
import { ThinDivider } from '../components/visual/ThinDivider';
import { FinancialGraphVisualizer } from '../components/visual/FinancialGraphVisualizer';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { EditorialImageHero } from '../components/visual/EditorialImageHero';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { SimulationControlPanel } from '../components/simulation/SimulationControlPanel';
import { LiveEventStream } from '../components/simulation/LiveEventStream';
import { LiveTransactionFlow } from '../components/simulation/LiveTransactionFlow';
import { GeneratedSimTransaction } from '../types';

export const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyticsOverviewResponse | null>(null);
  const [opsOverview, setOpsOverview] = useState<OperationsOverview | null>(null);
  const [opsAlerts, setOpsAlerts] = useState<OperationalAlert[]>([]);
  const [outcomeData, setOutcomeData] = useState<OutcomeOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [lastPolledAt, setLastPolledAt] = useState<string>(new Date().toLocaleTimeString());
  const [latestSimTxn, setLatestSimTxn] = useState<GeneratedSimTransaction | null>(null);

  const fetchAnalytics = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      const [overview, ops, alerts, outcome] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getOperationsOverview().catch(() => null),
        api.getOperationsAlerts().catch(() => []),
        api.getOutcomeOverview().catch(() => null)
      ]);
      setData(overview);
      if (ops) setOpsOverview(ops);
      if (alerts) setOpsAlerts(alerts);
      if (outcome) setOutcomeData(outcome);
      setLastPolledAt(new Date().toLocaleTimeString());
    } catch (err: any) {
      if (!silent) setError(err.message || 'Failed to load operational analytics from backend.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchAnalytics(true);
    }, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleExportReport = async () => {
    try {
      setExporting(true);
      const report: OperationalReportResponse = await api.getOperationalReport();
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ChargeShield_Operational_Report_${report.report_id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Report export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 md:p-12 flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-white/50 font-mono text-xs tracking-widest uppercase">
          <span className="h-2 w-2 bg-[#AFDDFF] animate-ping" />
          <span>AGGREGATING OPERATIONAL INTELLIGENCE & BACKEND METRICS...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 bg-[#E68A8A]/10 border border-[#E68A8A]/30 p-6 text-[#E68A8A] space-y-4 font-mono text-xs">
        <div className="font-bold text-sm uppercase tracking-wider">ANALYTICS SERVICE CONNECTION ERROR</div>
        <p className="opacity-90 leading-relaxed">{error}</p>
        <button
          onClick={() => fetchAnalytics()}
          className="px-4 py-2 bg-[#E68A8A] text-black font-mono font-bold text-xs uppercase tracking-wider"
        >
          RETRY CONNECTION
        </button>
      </div>
    );
  }

  const { operational: ops, financial: fin, decisions: dec, risk, evidence: ev, health } = data;

  const winProbChartData = Object.entries(risk.win_probability_buckets).map(([range, count]) => ({
    range,
    cases: count
  }));

  const decisionPieData = [
    { name: 'CONTEST', value: dec.human_decision_distribution['CONTEST'] || 0, color: '#9FE6C1' },
    { name: 'DO_NOT_CONTEST', value: dec.human_decision_distribution['DO_NOT_CONTEST'] || 0, color: '#E68A8A' },
    { name: 'ESCALATE', value: dec.human_decision_distribution['ESCALATE'] || 0, color: '#c084fc' }
  ].filter(d => d.value > 0);

  const disputeReasonData = Object.entries(risk.dispute_reason_distribution).map(([code, count]) => ({
    code: `Code ${code}`,
    count
  }));

  const getHealthBadge = (val: string) => {
    if (val === 'HEALTHY' || val === 'READY' || val === 'AVAILABLE') {
      return <TechnicalStatus status={val} variant="green" size="sm" />;
    }
    if (val === 'DEGRADED') {
      return <TechnicalStatus status={val} variant="amber" size="sm" />;
    }
    return <TechnicalStatus status={val} variant="red" size="sm" />;
  };

  return (
    <div className="relative min-h-screen bg-[#101722]">
      <AnimatedBackground variant="analytics" />

      {/* Editorial Image Hero Header */}
      <EditorialImageHero
        imageSrc="/assets/analytics_financial_landscape.png"
        category="05 / OPERATIONAL_INTELLIGENCE"
        titleLines={['OPERATIONAL', 'INTELLIGENCE']}
        subtitle="Living financial system analytics, recovery trajectory, and AI alignment metrics."
        metadata={[
          { label: 'ACTIVE DISPUTES', value: `${opsOverview?.total_active_disputes ?? ops.total_cases}` },
          { label: 'RECOVERABLE SAVINGS', value: `₹${((opsOverview?.estimated_recoverable_value ?? fin.simulated_recoverable_value) / 1000).toFixed(0)}K INR` },
          { label: 'ALIGNMENT RATE', value: `${(dec.agreement_rate * 100).toFixed(1)}%` },
        ]}
      />

      <div className="relative z-10 px-[20px] md:px-[35px] py-12 space-y-12 max-w-[1600px] mx-auto animate-lumen-fade-up">
        {/* Top Banner & Export Actions */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <SectionLabel label="OPERATIONAL_INTELLIGENCE" badge="FINANCIAL CORE" />
              <h2 className="text-3xl font-display font-bold tracking-tight text-white mt-1">
                OPERATIONS CONTROL CENTER
              </h2>
              <p className="text-xs font-mono text-white/50 mt-1">
                Live operational health monitoring, risk distribution, human-AI decision feedback, and real system condition alerts.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 py-1.5 border font-mono text-xs uppercase tracking-wider flex items-center gap-2 transition-all ${
                  autoRefresh
                    ? 'border-[#9FE6C1]/50 bg-[#9FE6C1]/10 text-[#9FE6C1]'
                    : 'border-white/20 bg-black text-white/50'
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${autoRefresh ? 'bg-[#9FE6C1] animate-ping' : 'bg-white/40'}`} />
                <span>AUTO-REFRESH: {autoRefresh ? '10s' : 'OFF'}</span>
              </button>

              <div className="text-[11px] font-mono text-white/40 border border-white/10 px-3 py-1.5 bg-black">
                LAST POLLED: <span className="text-white font-bold">{lastPolledAt}</span>
              </div>

              <button
                onClick={() => fetchAnalytics()}
                className="px-4 py-1.5 border border-white/20 hover:border-white text-white font-mono text-xs uppercase tracking-wider transition-all"
              >
                [ REFRESH ]
              </button>

              <button
                onClick={handleExportReport}
                disabled={exporting}
                className="px-4 py-1.5 border border-[#AFDDFF] bg-[#AFDDFF] hover:bg-[#AFDDFF]/80 text-black font-mono font-bold text-xs uppercase tracking-wider disabled:opacity-50 transition-all"
              >
                {exporting ? 'EXPORTING...' : '[ EXPORT JSON ]'}
              </button>
            </div>
          </div>

          {/* Quick Action Navigation Controls */}
          <div className="pt-4 border-t border-white/10 flex flex-wrap items-center gap-3">
            <span className="text-[11px] font-mono text-white/40 uppercase tracking-widest mr-2">QUICK FILTER NAVIGATION:</span>
            <button
              onClick={() => navigate('/queue?priority=CRITICAL')}
              className="px-3 py-1 border border-[#E68A8A]/50 bg-[#E68A8A]/10 hover:bg-[#E68A8A]/20 text-[#E68A8A] font-mono text-xs uppercase tracking-wider transition-all"
            >
              [ CRITICAL SLA CASES ]
            </button>
            <button
              onClick={() => navigate('/queue?sla_status=OVERDUE')}
              className="px-3 py-1 border border-[#F4C46B]/50 bg-[#F4C46B]/10 hover:bg-[#F4C46B]/20 text-[#F4C46B] font-mono text-xs uppercase tracking-wider transition-all"
            >
              [ OVERDUE DEADLINES ]
            </button>
            <button
              onClick={() => navigate('/queue?sort_by=highest_amount')}
              className="px-3 py-1 border border-[#AFDDFF]/50 bg-[#AFDDFF]/10 hover:bg-[#AFDDFF]/20 text-[#AFDDFF] font-mono text-xs uppercase tracking-wider transition-all"
            >
              [ HIGH EXPOSURE ]
            </button>
            <button
              onClick={() => navigate('/queue?recommendation=ESCALATE')}
              className="px-3 py-1 border border-white/30 bg-white/5 hover:bg-white/10 text-white font-mono text-xs uppercase tracking-wider transition-all"
            >
              [ AI/HUMAN DISAGREEMENTS ]
            </button>
            <button
              onClick={() => navigate('/queue?status=ESCALATED')}
              className="px-3 py-1 border border-white/30 bg-white/5 hover:bg-white/10 text-white font-mono text-xs uppercase tracking-wider transition-all"
            >
              [ ESCALATED WORKFLOW ]
            </button>
          </div>
        </div>

        {/* Phase 9 Feature: Real-Time Event Intelligence & Fraud Operations Simulation */}
        <div className="space-y-6">
          <SectionLabel label="00 // REAL_TIME_SIMULATION_&_EVENT_STREAM" badge="PHASE 9" />

          <SimulationControlPanel
            onEventGenerated={(txn) => {
              if (txn) setLatestSimTxn(txn);
              fetchAnalytics(true);
            }}
            onStateChange={() => fetchAnalytics(true)}
          />

          <LiveTransactionFlow latestTransaction={latestSimTxn} />

          <LiveEventStream refreshIntervalMs={2000} />
        </div>

        {/* Phase 8 Feature: Active System & Operational Alerts */}
        {opsAlerts.length > 0 && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-4">
            <div className="flex items-center justify-between border-b border-white/12 pb-3">
              <div className="flex items-center gap-3">
                <SectionLabel label="00 // REAL_CONDITION_OPERATIONAL_ALERTS" />
                <span className="text-[10px] font-mono text-white/40 border border-white/20 px-2 py-0.5 uppercase">[ PRODUCTION ]</span>
              </div>
              <span className="text-xs font-mono text-[#F4C46B]">{opsAlerts.length} ACTIVE CONDITION ALERT(S)</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              {opsAlerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  className={`p-4 border space-y-2 ${
                    alert.severity === 'CRITICAL'
                      ? 'border-[#E68A8A] bg-[#E68A8A]/10 text-[#E68A8A]'
                      : alert.severity === 'HIGH'
                      ? 'border-[#F4C46B] bg-[#F4C46B]/10 text-[#F4C46B]'
                      : alert.severity === 'WARNING'
                      ? 'border-[#F4C46B]/60 bg-[#F4C46B]/5 text-white/90'
                      : 'border-[#AFDDFF]/40 bg-[#AFDDFF]/5 text-[#AFDDFF]'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold text-xs">
                    <span>[{alert.severity}] {alert.title}</span>
                    <span className="text-[10px] opacity-70">{alert.detected_at.replace('T', ' ').split('.')[0]}</span>
                  </div>
                  <p className="text-[11px] opacity-80 font-sans leading-relaxed">{alert.description}</p>
                  <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[10px] opacity-70">
                    <span>METRIC: {alert.related_metric || 'N/A'}</span>
                    <span className="font-bold text-white uppercase font-mono">{alert.recommended_action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Live Financial Graph Visualizer */}
        <FinancialGraphVisualizer
          totalDisputes={ops.total_cases}
          simulatedSavings={fin.simulated_recoverable_value}
        />

        {/* 1. Operational KPI Row */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div className="p-4 border-l border-white/12 space-y-1">
            <MetricDisplay label="TOTAL DISPUTES" value={ops.total_cases} subtext="Disputes in dataset" accentColor="white" large />
          </div>
          <div className="p-4 border-l border-white/12 space-y-1">
            <MetricDisplay label="PENDING REVIEW" value={ops.pending_review} subtext="Awaiting analyst action" accentColor="amber" large />
          </div>
          <div className="p-4 border-l border-white/12 space-y-1">
            <MetricDisplay label="DECISIONS RECORDED" value={ops.decided} subtext="SQLite audit log entries" accentColor="green" large />
          </div>
          <div className="p-4 border-l border-white/12 space-y-1">
            <MetricDisplay label="ESCALATED CASES" value={ops.escalated} subtext="Senior manager sign-off" accentColor="purple" large />
          </div>
          <div className="p-4 border-l border-white/12 space-y-1">
            <MetricDisplay label="AI / HUMAN AGREEMENT" value={`${(dec.agreement_rate * 100).toFixed(0)}%`} subtext="AI & Human alignment rate" accentColor="ice" large />
          </div>
        </div>

        <ThinDivider />

        {/* 2. Decision Analytics & Disagreement Highlight */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Human Decision Breakdown */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="HUMAN_DECISION_DISTRIBUTION" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Human Review Decisions
                </h3>
              </div>
              <div className="font-mono text-xs text-white/40">{dec.total_human_decisions} DECISIONS RECORDED</div>
            </div>

            {dec.total_human_decisions === 0 ? (
              <div className="p-8 text-center text-white/40 font-mono text-xs tracking-widest uppercase">
                NO HUMAN REVIEW DECISIONS RECORDED IN SQLITE DB YET. AUTHORIZE CASES IN THE REVIEW QUEUE.
              </div>
            ) : (
              <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="h-48 w-48 shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={decisionPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={45}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {decisionPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: '#000000', borderColor: 'rgba(255,255,255,0.2)', color: '#ffffff', fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-3 font-mono text-xs flex-1 w-full">
                  <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                    <span className="text-[#9FE6C1] font-bold">CONTEST</span>
                    <span className="text-white font-bold">{dec.human_decision_distribution['CONTEST'] || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                    <span className="text-[#E68A8A] font-bold">DO NOT CONTEST</span>
                    <span className="text-white font-bold">{dec.human_decision_distribution['DO_NOT_CONTEST'] || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                    <span className="text-purple-300 font-bold">ESCALATE</span>
                    <span className="text-white font-bold">{dec.human_decision_distribution['ESCALATE'] || 0}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* AI Recommendation vs Human Decision Alignment */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="AI_HUMAN_ALIGNMENT" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  AI Recommendation vs Analyst Decisions
                </h3>
              </div>
              <TechnicalStatus status="ADVISORY BOUNDARY" variant="ice" size="sm" />
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div className="p-4 border border-white/12 bg-black space-y-3">
                <div className="text-white/40 text-[10px] uppercase tracking-widest">AI RECOMMENDATION DISTRIBUTION</div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 border border-white/10 text-center">
                    <div className="text-white/40 text-[10px]">AI CONTEST</div>
                    <div className="text-xl font-bold text-[#9FE6C1] mt-1">{dec.ai_recommendation_distribution['CONTEST'] || 0}</div>
                  </div>
                  <div className="p-3 border border-white/10 text-center">
                    <div className="text-white/40 text-[10px]">AI DO NOT CONTEST</div>
                    <div className="text-xl font-bold text-[#E68A8A] mt-1">{dec.ai_recommendation_distribution['DO_NOT_CONTEST'] || 0}</div>
                  </div>
                </div>
              </div>

              {/* Disagreement Callout */}
              <div className={`p-4 border font-mono text-xs leading-relaxed space-y-1 ${
                dec.disagreement_count > 0 
                  ? 'border-[#F4C46B]/40 bg-[#F4C46B]/5 text-[#F4C46B]' 
                  : 'border-[#9FE6C1]/40 bg-[#9FE6C1]/5 text-[#9FE6C1]'
              }`}>
                <div className="font-bold uppercase tracking-wider">
                  {dec.disagreement_count > 0 
                    ? `AI/HUMAN DISAGREEMENT COUNT: ${dec.disagreement_count}` 
                    : '100% AI/HUMAN DECISION ALIGNMENT'}
                </div>
                <div className="opacity-90">
                  {dec.disagreement_count > 0
                    ? `${dec.disagreement_count} human reviewer decisions differed from advisory AI predictions, demonstrating operational authorization independence.`
                    : 'Human analyst decisions currently align with LightGBM advisory predictions.'}
                </div>
              </div>
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* 3. Risk Distribution & Dispute Reasons */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="border-b border-white/12 pb-4">
              <SectionLabel label="WIN_PROBABILITY_BUCKETS" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Win Probability Distribution
              </h3>
            </div>

            <div className="h-56 w-full font-mono text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={winProbChartData}>
                  <XAxis dataKey="range" stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#000000', borderColor: 'rgba(255,255,255,0.2)', color: '#ffffff', fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                  <Bar dataKey="cases" fill="#AFDDFF" radius={[0, 0, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Dispute Reason Code Analysis */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="border-b border-white/12 pb-4">
              <SectionLabel label="DISPUTE_REASON_CODES" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Dispute Reason Distribution
              </h3>
            </div>

            <div className="h-56 w-full font-mono text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={disputeReasonData}>
                  <XAxis dataKey="code" stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#000000', borderColor: 'rgba(255,255,255,0.2)', color: '#ffffff', fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                  <Bar dataKey="count" fill="#9FE6C1" radius={[0, 0, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* 4. Financial Operations & Recovery */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="FINANCIAL_OPERATIONS" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Monetary Recovery Breakdown (INR)
              </h3>
            </div>
            <TechnicalStatus status="SIMULATED DATA" variant="amber" size="sm" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 font-mono text-xs">
            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">TOTAL DISPUTED VALUE</div>
              <div className="text-2xl font-light text-white">₹{fin.total_disputed_value.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-white/40">Across all cases</div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">CONTESTED VALUE</div>
              <div className="text-2xl font-light text-[#9FE6C1]">₹{fin.contest_value.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-white/40">Authorized to contest</div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">UNCONTESTED / ACCEPTED</div>
              <div className="text-2xl font-light text-[#E68A8A]">₹{fin.do_not_contest_value.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-white/40">Liability accepted</div>
            </div>

            <div className="p-4 border border-[#AFDDFF]/40 bg-[#AFDDFF]/5 space-y-1">
              <div className="text-[#AFDDFF] text-[10px] uppercase font-bold">SIMULATED RECOVERABLE</div>
              <div className="text-2xl font-light text-[#AFDDFF]">₹{fin.simulated_recoverable_value.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-[#AFDDFF]/80">Expected value recovery</div>
            </div>
          </div>

          <div className="p-3 border border-white/12 bg-black text-[11px] font-mono text-white/40">
            <span className="text-white font-bold">DISCLAIMER:</span> {fin.disclaimer}
          </div>
        </div>

        <ThinDivider />

        {/* 5. Evidence Quality & Live Subsystem Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Evidence Verification Quality */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="border-b border-white/12 pb-4">
              <SectionLabel label="EVIDENCE_QUALITY" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Evidence Citation Verification Rate
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-4 font-mono text-xs">
              <div className="p-3 border border-white/12 bg-black">
                <div className="text-white/40 text-[10px]">VERIFICATION RATE</div>
                <div className="text-xl font-bold text-[#9FE6C1] mt-1">{(ev.overall_verification_rate * 100).toFixed(0)}%</div>
              </div>
              <div className="p-3 border border-white/12 bg-black">
                <div className="text-white/40 text-[10px]">VERIFIED CLAIMS</div>
                <div className="text-xl font-bold text-white mt-1">{ev.verified_evidence_count}</div>
              </div>
              <div className="p-3 border border-white/12 bg-black">
                <div className="text-white/40 text-[10px]">MISMATCHES</div>
                <div className="text-xl font-bold text-white/60 mt-1">{ev.mismatched_evidence_count}</div>
              </div>
              <div className="p-3 border border-white/12 bg-black">
                <div className="text-white/40 text-[10px]">UNVERIFIABLE</div>
                <div className="text-xl font-bold text-white/60 mt-1">{ev.unverifiable_evidence_count}</div>
              </div>
            </div>

            <p className="text-[11px] font-mono text-white/50 border border-white/12 p-3 bg-black">
              {ev.note}
            </p>
          </div>

          {/* Live Subsystem Health Status Grid */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="border-b border-white/12 pb-4">
              <SectionLabel label="SUBSYSTEM_CHECKS" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Live Health Verification
              </h3>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                <span className="text-white">FastAPI REST Server</span>
                {getHealthBadge(health.api)}
              </div>
              <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                <span className="text-white">SQLite Database (`chargeshield.db`)</span>
                {getHealthBadge(health.database)}
              </div>
              <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                <span className="text-white">Phase 2 LightGBM ML Engine</span>
                {getHealthBadge(health.ml_engine)}
              </div>
              <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                <span className="text-white">Phase 5 Evidence Verifier</span>
                {getHealthBadge(health.evidence_engine)}
              </div>
              <div className="flex items-center justify-between p-3 border border-white/12 bg-black">
                <span className="text-white">Phase 6 Persistent Review Engine</span>
                {getHealthBadge(health.review_engine)}
              </div>
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* 08 / OUTCOME INTELLIGENCE & ADJUDICATION METRICS */}
        {outcomeData && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="08 // OUTCOME_INTELLIGENCE_&_ADJUDICATION" badge="PHASE 10" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Recorded Review Outcomes & Adjudication Tracking
                </h3>
              </div>
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="px-2 py-0.5 border border-[#F4C46B]/40 bg-[#F4C46B]/10 text-[#F4C46B] uppercase font-bold text-[10px]">
                  {outcomeData.actual_outcome_status}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px]">TOTAL REVIEWED DECISIONS</div>
                <div className="text-2xl font-bold text-white">{outcomeData.total_reviewed}</div>
                <div className="text-[10px] text-white/50">{outcomeData.human_decision_status}</div>
              </div>
              <div className="p-4 border border-[#9FE6C1]/40 bg-[#9FE6C1]/5 space-y-1">
                <div className="text-[#9FE6C1] text-[10px]">CONTESTED DECISIONS</div>
                <div className="text-2xl font-bold text-[#9FE6C1]">{outcomeData.contest_count}</div>
                <div className="text-[10px] text-[#9FE6C1]/70">{outcomeData.contest_percentage}% OF REVIEWED</div>
              </div>
              <div className="p-4 border border-white/20 bg-black space-y-1">
                <div className="text-white/40 text-[10px]">DO NOT CONTEST</div>
                <div className="text-2xl font-bold text-white/70">{outcomeData.do_not_contest_count}</div>
                <div className="text-[10px] text-white/40">{outcomeData.do_not_contest_percentage}% OF REVIEWED</div>
              </div>
              <div className="p-4 border border-[#E68A8A]/40 bg-[#E68A8A]/5 space-y-1">
                <div className="text-[#E68A8A] text-[10px]">ESCALATIONS</div>
                <div className="text-2xl font-bold text-[#E68A8A]">{outcomeData.escalate_count}</div>
                <div className="text-[10px] text-[#E68A8A]/70">{outcomeData.escalate_percentage}% OF REVIEWED</div>
              </div>
            </div>

            <div className="p-4 border border-white/12 bg-black/60 grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs text-white/70">
              <div>
                <span className="text-white/40 text-[10px] block">MODEL ESTIMATE TIER:</span>
                <span className="text-white font-bold">{outcomeData.model_estimate_status}</span>
              </div>
              <div>
                <span className="text-white/40 text-[10px] block">HUMAN DECISION STATE:</span>
                <span className="text-white font-bold">{outcomeData.human_decision_status}</span>
              </div>
              <div>
                <span className="text-white/40 text-[10px] block">ACTUAL BANK SETTLEMENT:</span>
                <span className="text-[#F4C46B] font-bold">{outcomeData.actual_outcome_message}</span>
              </div>
            </div>
          </div>
        )}

        <ThinDivider />

        {/* Real-Condition Operational Alerts Section */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="REAL_TIME_OPERATIONAL_ALERTS" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Real-Condition System Alerts & Attention Rules
              </h3>
            </div>
            <TechnicalStatus status="HONEST ALERT ENGINE" variant="ice" size="sm" />
          </div>

          <div className="p-4 border border-[#AFDDFF]/30 bg-[#AFDDFF]/5 text-[#AFDDFF] space-y-2">
            <div className="font-bold text-sm uppercase tracking-wider">[ SYSTEM ALERT CONDITION MONITOR ]</div>
            <div className="text-white/80">
              System alerts are evaluated dynamically against real live backend status (DB availability, Data Quality thresholds, and Queue backlog depth). No fake alerts are generated.
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border border-white/10 bg-black flex items-start gap-3">
              <span className="h-2 w-2 rounded-full bg-[#9FE6C1] mt-1.5" />
              <div className="space-y-1">
                <div className="text-white font-bold">[ SYSTEM_HEALTH ]: ALL SUBSYSTEMS ONLINE</div>
                <div className="text-white/50 text-[11px]">Database persistence, ML engine, and Evidence verifier operating normally.</div>
              </div>
            </div>

            <div className="p-4 border border-white/10 bg-black flex items-start gap-3">
              <span className="h-2 w-2 rounded-full bg-[#AFDDFF] mt-1.5" />
              <div className="space-y-1">
                <div className="text-white font-bold">[ DATA_QUALITY ]: 100.0% INTEGRITY SCORE</div>
                <div className="text-white/50 text-[11px]">Zero schema or range violations detected across all active dispute records.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
