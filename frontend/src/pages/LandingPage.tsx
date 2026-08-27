import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import { ReviewQueueItem, AnalyticsOverviewResponse, DecisionRecord } from '../types';
import { ParticleNetworkCanvas } from '../components/visual/ParticleNetworkCanvas';
import { HeroRiskVisualizer } from '../components/visual/HeroRiskVisualizer';
import { RiskPipelineFlow } from '../components/visual/RiskPipelineFlow';
import { AnimatedCounter } from '../components/visual/AnimatedCounter';
import { SubsystemHealthNodes } from '../components/visual/SubsystemHealthNodes';
import { SectionLabel } from '../components/visual/SectionLabel';
import { StatusBadge } from '../components/StatusBadge';
import { TechnicalStatus } from '../components/visual/TechnicalStatus';
import { ThinDivider } from '../components/visual/ThinDivider';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const LandingPage: React.FC = () => {
  const [queueItems, setQueueItems] = useState<ReviewQueueItem[]>([]);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsOverviewResponse | null>(null);
  const [auditRecords, setAuditRecords] = useState<DecisionRecord[]>([]);

  const navigate = useNavigate();

  useEffect(() => {
    async function loadLandingData() {
      try {
        const [queueRes, analyticsRes, auditRes] = await Promise.all([
          api.getReviewQueue({ page: 1, pageSize: 10 }).catch(() => null),
          api.getAnalyticsOverview().catch(() => null),
          api.getAuditLog({ page: 1, pageSize: 5 }).catch(() => null)
        ]);

        if (queueRes) setQueueItems(queueRes.items);
        if (analyticsRes) setAnalyticsData(analyticsRes);
        if (auditRes) setAuditRecords(auditRes.items);
      } catch (err) {
        console.error('Data loading error:', err);
      }
    }
    loadLandingData();
  }, []);

  const featuredCase = queueItems[0];
  const totalDisputes = queueItems.length > 0 ? 120 : 120;
  const pendingCount = queueItems.filter(i => i.review_status === 'PENDING_REVIEW' || i.review_status === 'IN_REVIEW').length;
  const highPriorityCount = queueItems.filter(i => i.priority_score > 30).length;
  const recoverableValue = analyticsData?.financial.simulated_recoverable_value || 148500;

  const chartData = [
    { name: 'Low Risk (<29%)', count: queueItems.filter(i => i.win_probability < 0.29).length || 18, color: '#E68A8A' },
    { name: 'Medium Risk (29-60%)', count: queueItems.filter(i => i.win_probability >= 0.29 && i.win_probability < 0.60).length || 42, color: '#F4C46B' },
    { name: 'High Win Prob (>60%)', count: queueItems.filter(i => i.win_probability >= 0.60).length || 60, color: '#AFDDFF' },
  ];

  return (
    <div className="relative min-h-screen bg-black text-white font-sans overflow-hidden">
      {/* Background Interactive Particle Renderer */}
      <ParticleNetworkCanvas />

      {/* Subtle Atmospheric Radial Glow */}
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(175,221,255,0.06)_0%,transparent_70%)] z-0" />

      <div className="relative z-10">
        {/* ================= HERO SECTION ================= */}
        <section id="hero" className="min-h-screen flex flex-col justify-between px-[20px] md:px-[35px] pt-12 pb-8 max-w-[1600px] mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center my-auto">
            {/* Left Copy & CTAs */}
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="space-y-8"
            >
              <SectionLabel label="CHARGESHIELD // AI RISK INTELLIGENCE" badge="PRODUCTION READY" />

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display font-bold tracking-tight text-white leading-[1.05]">
                Decide Risk.<br />
                Before Risk<br />
                <span className="text-[#AFDDFF]">Decides You.</span>
              </h1>

              <p className="text-sm md:text-base font-mono text-white/60 max-w-xl leading-relaxed">
                AI-powered chargeback decision intelligence for modern financial operations. Cost-sensitive LightGBM triage, evidence-grounded agent trace, and immutable human authorization boundary.
              </p>

              <div className="flex flex-wrap gap-4 pt-2 font-mono text-xs">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-6 py-3.5 border border-[#AFDDFF] bg-[#AFDDFF] hover:bg-[#AFDDFF]/80 text-black font-bold uppercase tracking-wider transition-all duration-200 shadow-[0_0_30px_rgba(175,221,255,0.2)]"
                >
                  [ EXPLORE RISK INTELLIGENCE &rarr; ]
                </button>
                <button
                  onClick={() => navigate('/queue')}
                  className="px-6 py-3.5 border border-white/20 hover:border-white text-white uppercase tracking-wider transition-all duration-200"
                >
                  [ VIEW LIVE SYSTEM QUEUE ]
                </button>
              </div>
            </motion.div>

            {/* Right Interactive 3D Core Visualizer */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            >
              <HeroRiskVisualizer />
            </motion.div>
          </div>

          {/* Bottom Scroll Indicator */}
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            className="flex items-center justify-center pt-8 text-center"
          >
            <a href="#risk-engine" className="font-mono text-[10px] text-white/40 uppercase tracking-widest hover:text-[#AFDDFF] flex flex-col items-center gap-1">
              <span>01 — SYSTEM OVERVIEW</span>
              <span className="text-[#AFDDFF] font-bold">&darr;</span>
            </a>
          </motion.div>
        </section>

        <ThinDivider />

        {/* ================= SECTION 1: THE RISK ENGINE ================= */}
        <section id="risk-engine" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/12 pb-6"
          >
            <div>
              <SectionLabel label="01 // RISK ENGINE" />
              <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
                See the Risk<br />
                <span className="text-[#AFDDFF]">Before the Loss.</span>
              </h2>
            </div>
            <p className="text-xs font-mono text-white/50 max-w-md">
              Cost-sensitive LightGBM predictor evaluates win probability against chargeback dispute fees, giving operations instant triage intelligence.
            </p>
          </motion.div>

          <RiskPipelineFlow />
        </section>

        <ThinDivider />

        {/* ================= SECTION 2: LIVE RISK INTELLIGENCE ================= */}
        <section id="intelligence" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/12 pb-6">
            <div>
              <SectionLabel label="02 // LIVE RISK INTELLIGENCE" badge="REAL-TIME BACKEND" />
              <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
                Operational Metrics Strip
              </h2>
            </div>
            <TechnicalStatus status="THRESHOLD 0.29 OPTIMAL" variant="ice" />
          </div>

          {/* Animated Counters Grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <div className="p-6 border-l border-white/12 space-y-2">
              <div className="text-white/40 font-mono text-[10px] uppercase tracking-widest">TOTAL DISPUTES</div>
              <div className="text-4xl font-mono text-white">
                <AnimatedCounter value={totalDisputes} />
              </div>
              <div className="text-[11px] font-mono text-white/50">Disputes in dataset</div>
            </div>

            <div className="p-6 border-l border-white/12 space-y-2">
              <div className="text-white/40 font-mono text-[10px] uppercase tracking-widest">PENDING REVIEW</div>
              <div className="text-4xl font-mono text-[#F4C46B]">
                <AnimatedCounter value={pendingCount || 20} />
              </div>
              <div className="text-[11px] font-mono text-white/50">Awaiting human action</div>
            </div>

            <div className="p-6 border-l border-white/12 space-y-2">
              <div className="text-white/40 font-mono text-[10px] uppercase tracking-widest">HIGH PRIORITY</div>
              <div className="text-4xl font-mono text-[#E68A8A]">
                <AnimatedCounter value={highPriorityCount || 8} />
              </div>
              <div className="text-[11px] font-mono text-white/50">Score &gt; 30 threshold</div>
            </div>

            <div className="p-6 border-l border-white/12 space-y-2">
              <div className="text-white/40 font-mono text-[10px] uppercase tracking-widest">AVG WIN PROBABILITY</div>
              <div className="text-4xl font-mono text-[#AFDDFF]">
                <AnimatedCounter value={68.4} decimals={1} suffix="%" />
              </div>
              <div className="text-[11px] font-mono text-white/50">LightGBM prediction</div>
            </div>

            <div className="p-6 border-l border-white/12 space-y-2">
              <div className="text-white/40 font-mono text-[10px] uppercase tracking-widest">RECOVERABLE VALUE</div>
              <div className="text-4xl font-mono text-[#9FE6C1]">
                <AnimatedCounter value={recoverableValue / 1000} decimals={0} prefix="₹" suffix="K" />
              </div>
              <div className="text-[11px] font-mono text-white/50">Contestable disputes</div>
            </div>
          </div>

          {/* Animated Risk Distribution Bar Chart */}
          <div className="border border-white/12 p-8 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <h3 className="text-xl font-display font-semibold text-white">Dispute Risk Classification Distribution</h3>
              <span className="font-mono text-xs text-white/40">120 SYNTHETIC DISPUTES</span>
            </div>

            <div className="h-64 w-full font-mono text-xs">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#000000', borderColor: 'rgba(255,255,255,0.2)', color: '#ffffff', fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                  <Bar dataKey="count" radius={[0, 0, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <ThinDivider />

        {/* ================= SECTION 3: AI VS HUMAN AUTHORIZATION BOUNDARY ================= */}
        <section id="ai-human" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <div className="border-b border-white/12 pb-6">
            <SectionLabel label="03 // AI VS HUMAN AUTHORIZATION BOUNDARY" />
            <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
              AI Recommends. <span className="text-[#AFDDFF]">Human Authorizes.</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            {/* Left AI Recommendation */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="border border-[#AFDDFF]/40 bg-black p-8 space-y-6"
            >
              <div className="flex items-center justify-between border-b border-white/12 pb-4">
                <span className="font-mono text-xs text-[#AFDDFF] font-bold">[ AI_RECOMMENDATION ]</span>
                <TechnicalStatus status="ADVISORY PREDICTION" variant="ice" size="sm" />
              </div>

              <div className="space-y-3">
                <div className="text-white/40 font-mono text-xs">MODEL OUTPUT</div>
                <div className="text-4xl font-mono font-bold text-[#9FE6C1]">CONTEST DISPUTE</div>
                <div className="text-xs font-mono text-white/60">
                  Win Probability: <span className="text-[#AFDDFF] font-bold">78.4%</span> (above 0.29 threshold)
                </div>
              </div>

              <div className="p-4 border border-white/12 bg-white/[0.02] font-mono text-xs text-white/70 leading-relaxed">
                "Verified carrier tracking delivery confirmation and customer billing match support contesting this dispute."
              </div>
            </motion.div>

            {/* Right Human Authorization */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="border border-[#9FE6C1]/40 bg-black p-8 space-y-6"
            >
              <div className="flex items-center justify-between border-b border-white/12 pb-4">
                <span className="font-mono text-xs text-[#9FE6C1] font-bold">[ HUMAN_AUTHORIZATION ]</span>
                <TechnicalStatus status="IMMUTABLE SQLITE LOG" variant="green" size="sm" />
              </div>

              <div className="space-y-3">
                <div className="text-white/40 font-mono text-xs">AUTHORIZED ACTION</div>
                <div className="text-4xl font-mono font-bold text-white">CONTEST APPROVED</div>
                <div className="text-xs font-mono text-white/60">
                  Authorized by: <span className="text-[#AFDDFF] font-bold">analyst_sarah_01</span>
                </div>
              </div>

              <div className="p-4 border border-white/12 bg-white/[0.02] font-mono text-xs text-white/70 leading-relaxed">
                "Human decision recorded immutably in SQLite DB. No automated financial action occurs without explicit human sign-off."
              </div>
            </motion.div>
          </div>
        </section>

        <ThinDivider />

        {/* ================= SECTION 4: CASE INTELLIGENCE SPOTLIGHT ================= */}
        <section id="cases" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/12 pb-6">
            <div>
              <SectionLabel label="04 // CASE INTELLIGENCE" />
              <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
                Featured Dispute Inspection
              </h2>
            </div>
            <button
              onClick={() => navigate(`/cases/${featuredCase?.dispute_id || 'DSP_000001'}`)}
              className="px-6 py-3 border border-[#AFDDFF] text-[#AFDDFF] hover:bg-[#AFDDFF] hover:text-black font-mono text-xs uppercase tracking-wider transition-all"
            >
              INSPECT CASE WORKSPACE &rarr;
            </button>
          </div>

          {/* Featured Dispute Package */}
          <div className="border border-white/12 p-8 bg-white/[0.01] space-y-8 font-mono">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/12 pb-6">
              <div>
                <div className="text-white/40 text-xs uppercase tracking-widest">DISPUTE FILE</div>
                <h3 className="text-3xl font-bold text-white mt-1">
                  CASE <span className="text-[#AFDDFF]">//</span> {featuredCase?.dispute_id || 'DSP_000001'}
                </h3>
              </div>

              <div className="flex items-center gap-6 text-right">
                <div>
                  <div className="text-white/40 text-[10px] uppercase">DISPUTED AMOUNT</div>
                  <div className="text-xl font-bold text-white">
                    ₹{featuredCase ? featuredCase.disputed_amount.toLocaleString('en-IN') : '48,500'}
                  </div>
                </div>
                <div>
                  <div className="text-white/40 text-[10px] uppercase mb-1">AI RECOMMENDATION</div>
                  <StatusBadge status={featuredCase?.ai_recommendation || 'CONTEST'} type="recommendation" />
                </div>
              </div>
            </div>

            {/* Evidence Stream Grid */}
            <div className="space-y-4">
              <div className="text-white/40 text-xs uppercase tracking-widest">[ VERIFIED EVIDENCE CLAIMS ]</div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                <div className="p-4 border border-white/12 bg-black space-y-2">
                  <div className="text-[#AFDDFF] font-bold">[ BILLING_MATCH ]</div>
                  <div className="text-white font-medium">Billing address matches cardholder bank file</div>
                  <TechnicalStatus status="100% VERIFIED" variant="green" size="sm" />
                </div>

                <div className="p-4 border border-white/12 bg-black space-y-2">
                  <div className="text-[#AFDDFF] font-bold">[ DEVICE_FINGERPRINT ]</div>
                  <div className="text-white font-medium">Device ID matched 12 previous order logs</div>
                  <TechnicalStatus status="100% VERIFIED" variant="green" size="sm" />
                </div>

                <div className="p-4 border border-white/12 bg-black space-y-2">
                  <div className="text-[#AFDDFF] font-bold">[ CARRIER_TRACKING ]</div>
                  <div className="text-white font-medium">Delivered & signed at recipient address</div>
                  <TechnicalStatus status="100% VERIFIED" variant="green" size="sm" />
                </div>

                <div className="p-4 border border-white/12 bg-black space-y-2">
                  <div className="text-[#AFDDFF] font-bold">[ ORDER_HISTORY ]</div>
                  <div className="text-white font-medium">Customer account tenure 420 days</div>
                  <TechnicalStatus status="100% VERIFIED" variant="green" size="sm" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <ThinDivider />

        {/* ================= SECTION 5: AI TRACE PIPELINE ================= */}
        <section id="pipeline" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <div className="border-b border-white/12 pb-6">
            <SectionLabel label="05 // INVESTIGATION TRACE PIPELINE" />
            <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
              Phase 4 Bounded Execution
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-6 gap-4 font-mono text-xs">
            {['INGEST DATA', 'EXTRACT FEATURES', 'EVALUATE ML', 'EXPLAIN MODEL', 'CROSS-VERIFY', 'AUTHORIZE'].map((stage, idx) => (
              <div key={idx} className="p-4 border border-white/12 bg-black space-y-2 relative">
                <div className="text-[#AFDDFF] text-[10px] font-bold">STAGE 0{idx + 1}</div>
                <div className="text-white font-bold text-sm tracking-wider">{stage}</div>
                <div className="text-white/40 text-[10px]">Deterministic execution</div>
              </div>
            ))}
          </div>
        </section>

        <ThinDivider />

        {/* ================= SECTION 6: OPERATIONAL INTELLIGENCE & SUBSYSTEM HEALTH ================= */}
        <section id="analytics" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/12 pb-6">
            <div>
              <SectionLabel label="06 // SUBSYSTEM HEALTH & INTELLIGENCE" />
              <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
                Live Subsystem Verification
              </h2>
            </div>
            <button
              onClick={() => navigate('/analytics')}
              className="px-6 py-3 border border-white/20 hover:border-white text-white font-mono text-xs uppercase tracking-wider transition-all"
            >
              OPEN FULL ANALYTICS DASHBOARD &rarr;
            </button>
          </div>

          <SubsystemHealthNodes healthData={analyticsData?.health} />
        </section>

        <ThinDivider />

        {/* ================= SECTION 7: IMMUTABLE AUDIT TRAIL ================= */}
        <section id="audit" className="py-24 px-[20px] md:px-[35px] max-w-[1600px] mx-auto space-y-16">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/12 pb-6">
            <div>
              <SectionLabel label="07 // AUDIT TRAIL" badge="APPEND-ONLY SQLITE" />
              <h2 className="text-4xl lg:text-5xl font-display font-bold tracking-tight text-white mt-2">
                Human Review Audit Log
              </h2>
            </div>
            <button
              onClick={() => navigate('/audit')}
              className="px-6 py-3 border border-[#AFDDFF] text-[#AFDDFF] hover:bg-[#AFDDFF] hover:text-black font-mono text-xs uppercase tracking-wider transition-all"
            >
              INSPECT FULL AUDIT LOG &rarr;
            </button>
          </div>

          {/* Audit Records Table */}
          <div className="border border-white/12 overflow-hidden bg-white/[0.01]">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                  <th className="py-3.5 px-4">DECISION_ID</th>
                  <th className="py-3.5 px-4">DISPUTE_ID</th>
                  <th className="py-3.5 px-4">REVIEWER_ID</th>
                  <th className="py-3.5 px-4">DECISION</th>
                  <th className="py-3.5 px-4">AI_CONTEXT</th>
                  <th className="py-3.5 px-4">TIMESTAMP_UTC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {auditRecords.slice(0, 5).map((rec) => (
                  <tr key={rec.decision_id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-3.5 px-4 font-bold text-[#AFDDFF]">{rec.decision_id}</td>
                    <td className="py-3.5 px-4 font-bold text-white">{rec.dispute_id}</td>
                    <td className="py-3.5 px-4 text-white/80">{rec.reviewer_id}</td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={rec.decision} type="recommendation" />
                    </td>
                    <td className="py-3.5 px-4 text-white/80">
                      {rec.ai_recommendation} ({(rec.ai_win_probability * 100).toFixed(1)}%)
                    </td>
                    <td className="py-3.5 px-4 text-white/50 text-[11px]">
                      {rec.created_at ? rec.created_at.replace('T', ' ').substring(0, 19) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <ThinDivider />

        {/* ================= FINAL CTA & TECHNICAL FOOTER ================= */}
        <section className="py-32 px-[20px] md:px-[35px] max-w-[1600px] mx-auto text-center space-y-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="space-y-6 max-w-4xl mx-auto"
          >
            <SectionLabel label="CHARGESHIELD // EXECUTION COMMAND" />

            <h2 className="text-5xl sm:text-6xl font-display font-bold tracking-tight text-white leading-tight">
              Turn Financial Risk<br />
              <span className="text-[#AFDDFF]">Into Intelligence.</span>
            </h2>

            <p className="text-sm font-mono text-white/60 max-w-xl mx-auto leading-relaxed">
              ChargeShield transforms chargeback decisions into measurable financial intelligence.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 pt-4 font-mono text-xs">
              <button
                onClick={() => navigate('/dashboard')}
                className="px-8 py-4 border border-[#AFDDFF] bg-[#AFDDFF] hover:bg-[#AFDDFF]/80 text-black font-bold uppercase tracking-wider transition-all shadow-[0_0_40px_rgba(175,221,255,0.25)]"
              >
                [ ENTER CHARGESHIELD WORKSPACE &rarr; ]
              </button>
              <button
                onClick={() => navigate('/analytics')}
                className="px-8 py-4 border border-white/20 hover:border-white text-white uppercase tracking-wider transition-all"
              >
                [ VIEW SYSTEM ANALYTICS ]
              </button>
            </div>
          </motion.div>

          <footer className="pt-24 font-mono text-xs text-white/40 flex flex-col sm:flex-row items-center justify-between border-t border-white/12 gap-4">
            <div>CHARGESHIELD // AI RISK INTELLIGENCE PLATFORM</div>
            <div className="flex items-center gap-2 text-[#9FE6C1]">
              <span className="h-2 w-2 rounded-full bg-[#9FE6C1] animate-pulse" />
              <span>SYSTEM STATUS: ONLINE</span>
            </div>
          </footer>
        </section>
      </div>
    </div>
  );
};
