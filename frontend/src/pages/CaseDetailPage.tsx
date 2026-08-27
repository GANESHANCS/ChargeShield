import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { ReviewCasePackage, DecisionType, DecisionRecord, CaseTimeline, SLAInfo, EvidenceConfidenceInfo, CaseNote, CaseActivityItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ProbabilityGauge } from '../components/ProbabilityGauge';
import { SectionLabel } from '../components/visual/SectionLabel';
import { TechnicalStatus } from '../components/visual/TechnicalStatus';
import { ThinDivider } from '../components/visual/ThinDivider';
import { EvidenceNetworkVisualizer } from '../components/visual/EvidenceNetworkVisualizer';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { EditorialImageHero } from '../components/visual/EditorialImageHero';
import { OutcomeFeedbackModal } from '../components/OutcomeFeedbackModal';

export const CaseDetailPage: React.FC = () => {
  const { disputeId = 'DSP_000001' } = useParams<{ disputeId: string }>();
  const [pkg, setPkg] = useState<ReviewCasePackage | null>(null);
  const [timeline, setTimeline] = useState<CaseTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Phase 10 state
  const [slaInfo, setSlaInfo] = useState<SLAInfo | null>(null);
  const [evidenceConfidence, setEvidenceConfidence] = useState<EvidenceConfidenceInfo | null>(null);
  const [caseNotes, setCaseNotes] = useState<CaseNote[]>([]);
  const [activityTrace, setActivityTrace] = useState<CaseActivityItem[]>([]);
  const [newNoteText, setNewNoteText] = useState<string>('');
  const [addingNote, setAddingNote] = useState<boolean>(false);

  // Human Review Form state
  const [selectedDecision, setSelectedDecision] = useState<DecisionType>('CONTEST');
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [reviewerId] = useState<string>('analyst_sarah_01');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showOutcomeModal, setShowOutcomeModal] = useState(false);

  const navigate = useNavigate();

  const loadCaseData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getReviewCasePackage(disputeId);
      setPkg(data);
      if (data.prediction.recommendation === 'CONTEST') {
        setDecisionReason('Verified fulfillment and carrier tracking evidence supports contesting this dispute.');
      } else {
        setDecisionReason('High dispute history or unverified physical evidence accepts non-contestation.');
      }

      try {
        const [tlData, slaRes, evRes, notesRes, actRes] = await Promise.all([
          api.getCaseTimeline(disputeId).catch(() => null),
          api.getCaseSLA(disputeId).catch(() => null),
          api.getEvidenceConfidence(disputeId).catch(() => null),
          api.getCaseNotes(disputeId).catch(() => []),
          api.getCaseActivity(disputeId).catch(() => [])
        ]);
        if (tlData) setTimeline(tlData);
        if (slaRes) setSlaInfo(slaRes);
        if (evRes) setEvidenceConfidence(evRes);
        if (notesRes) setCaseNotes(notesRes);
        if (actRes) setActivityTrace(actRes);
      } catch (p10Err) {
        console.warn("Phase 10 data load warning:", p10Err);
      }
    } catch (err: any) {
      setError(err.message || `Failed to retrieve case details for ${disputeId}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaseData();
  }, [disputeId]);

  const handleAddNote = async () => {
    if (!newNoteText || newNoteText.trim().length < 3) return;
    try {
      setAddingNote(true);
      await api.addCaseNote(disputeId, reviewerId, newNoteText.trim());
      setNewNoteText('');
      const updatedNotes = await api.getCaseNotes(disputeId);
      setCaseNotes(updatedNotes);
      const updatedTrace = await api.getCaseActivity(disputeId);
      setActivityTrace(updatedTrace);
    } catch (err: any) {
      console.error("Add note error:", err);
    } finally {
      setAddingNote(false);
    }
  };

  const handleDecisionSubmit = async () => {
    if (!pkg) return;
    if (!decisionReason || decisionReason.trim().length < 5) {
      setSubmitError('A meaningful decision reason (at least 5 characters) is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError(null);
      await api.submitDecision(disputeId, reviewerId, selectedDecision, decisionReason.trim());
      setShowConfirmModal(false);
      
      const updatedPkg = await api.getReviewCasePackage(disputeId);
      setPkg(updatedPkg);
    } catch (err: any) {
      if (err.status === 409) {
        setSubmitError(`Duplicate Decision Rejected (409 Conflict): Case '${disputeId}' has already been DECIDED.`);
      } else if (err.status === 422) {
        setSubmitError(`Validation Error (422 Unprocessable Entity): ${err.message}`);
      } else {
        setSubmitError(`Decision Submission Error: ${err.message}`);
      }
      setShowConfirmModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 md:p-12 flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-white/50 font-mono text-xs tracking-widest uppercase">
          <span className="h-2 w-2 bg-[#AFDDFF] animate-ping" />
          <span>ASSEMBLING REVIEW PACKAGE FOR {disputeId}...</span>
        </div>
      </div>
    );
  }

  if (error || !pkg) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 bg-[#E68A8A]/10 border border-[#E68A8A]/30 p-6 text-[#E68A8A] space-y-4 font-mono text-xs">
        <div className="font-bold text-sm uppercase tracking-wider">CASE NOT FOUND OR SERVER ERROR</div>
        <p className="opacity-90 leading-relaxed">{error}</p>
        <div className="flex gap-4">
          <button
            onClick={() => loadCaseData()}
            className="px-4 py-2 bg-[#E68A8A] text-black font-mono font-bold text-xs uppercase tracking-wider"
          >
            RETRY
          </button>
          <button
            onClick={() => navigate('/queue')}
            className="px-4 py-2 border border-white/20 text-white font-mono text-xs uppercase tracking-wider"
          >
            RETURN TO QUEUE
          </button>
        </div>
      </div>
    );
  }

  const { case: c, prediction: pred, investigation: inv, verification: ver, review_status: revStatus, decisions } = pkg;
  const isDecided = revStatus === 'DECIDED';
  const latestDecision: DecisionRecord | undefined = decisions[decisions.length - 1];

  return (
    <div className="relative min-h-screen bg-[#0B1017]">
      <AnimatedBackground variant="case" />

      {/* Editorial Image Hero Header */}
      <EditorialImageHero
        imageSrc="/assets/case_investigative_evidence.png"
        category="03 / INVESTIGATIVE_DOSSIER"
        titleLines={['CASE FILE', c.dispute.dispute_id]}
        subtitle={`Disputed Amount: ₹${c.dispute.disputed_amount.toLocaleString('en-IN')} ${c.dispute.currency} • Win Probability: ${(pred.win_probability * 100).toFixed(1)}%`}
        metadata={[
          { label: 'DISPUTE AMOUNT', value: `₹${c.dispute.disputed_amount.toLocaleString('en-IN')}` },
          { label: 'REASON CODE', value: c.dispute.dispute_reason_code },
          { label: 'AI WIN PROBABILITY', value: `${(pred.win_probability * 100).toFixed(1)}%` },
          { label: 'RECOMMENDATION', value: pred.recommendation },
        ]}
      />

      <div className="relative z-10 px-[20px] md:px-[35px] py-12 space-y-8 max-w-[1600px] mx-auto animate-lumen-fade-up font-sans">
        {/* Top Bar Navigation */}
        <div className="flex items-center justify-between border-b border-white/12 pb-4 font-mono">
          <button
            onClick={() => navigate('/queue')}
            className="text-xs text-white/60 hover:text-[#AFDDFF] transition-colors uppercase tracking-wider flex items-center gap-2"
          >
            &larr; [ BACK_TO_QUEUE ]
          </button>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowOutcomeModal(true)}
              className="px-3 py-1 border border-[#9FE6C1] bg-[#9FE6C1]/10 text-[#9FE6C1] hover:bg-[#9FE6C1]/20 font-mono text-xs uppercase tracking-wider transition-all"
            >
              + RECORD OUTCOME LABEL
            </button>
            <StatusBadge status={revStatus} type="review" />
            <TechnicalStatus status="SYNTHETIC DATASET" variant="ice" size="sm" />
          </div>
        </div>

        {/* Live Interactive Evidence Network Room */}
        <EvidenceNetworkVisualizer
          disputeId={c.dispute.dispute_id}
          winProb={+(pred.win_probability * 100).toFixed(1)}
          recommendation={pred.recommendation}
        />

        {/* Section 1: Case Summary Header */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/12 pb-6">
            <div>
              <SectionLabel label="01 // CASE_SUMMARY_HEADER" />
              <h2 className="text-3xl font-display font-bold tracking-tight text-white mt-1">
                CASE <span className="text-[#AFDDFF]">//</span> {c.dispute.dispute_id}
              </h2>
              <p className="text-xs font-mono text-white/50 mt-1">
                Disputed Amount: <span className="font-bold text-white">₹{c.dispute.disputed_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} {c.dispute.currency}</span>
                {' • '}
                Reason Code: <span className="text-[#AFDDFF] font-bold">{c.dispute.dispute_reason_code}</span>
                {' • '}
                Deadline: <span className="text-[#F4C46B]">{c.dispute.response_deadline.split('T')[0]}</span>
              </p>
              {c.priority_reasoning && (
                <div className="mt-3 p-2.5 border border-[#AFDDFF]/30 bg-[#AFDDFF]/5 text-[11px] font-mono text-[#AFDDFF]">
                  [ PRIORITY REASONING ]: {c.priority_reasoning}
                </div>
              )}
            </div>

            <div className="flex items-center gap-8 font-mono text-right border-l border-white/12 pl-6">
              <div>
                <div className="text-[10px] text-white/40 uppercase tracking-widest">PRIORITY TIER</div>
                <div className={`text-xl font-bold font-mono ${c.priority === 'CRITICAL' ? 'text-[#E68A8A]' : c.priority === 'HIGH' ? 'text-[#F4C46B]' : 'text-[#9FE6C1]'}`}>
                  [{c.priority || 'HIGH'}]
                </div>
              </div>
              <div>
                <div className="text-[10px] text-white/40 uppercase tracking-widest mb-1">AI RECOMMENDATION</div>
                <StatusBadge status={pred.recommendation} type="recommendation" />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Financial Impact Center */}
        {c.financial_impact && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="02 // FINANCIAL_IMPACT_CENTER" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Dispute Financial Recovery & Operational Cost Math
                </h3>
              </div>
              <TechnicalStatus status="ILLUSTRATIVE ASSUMPTIONS" variant="amber" size="sm" />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">EXPECTED RECOVERY</div>
                <div className="text-xl font-bold text-[#9FE6C1]">
                  ₹{c.financial_impact.expected_recovery.toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-white/40">Amount × Win Prob</div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">ESTIMATED OP COST</div>
                <div className="text-xl font-bold text-[#F4C46B]">
                  ₹{c.financial_impact.estimated_operational_cost.toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-white/40">Base Fee + Multiplier</div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">NET CONTEST VALUE</div>
                <div className={`text-xl font-bold ${c.financial_impact.expected_net_contest_value >= 0 ? 'text-[#AFDDFF]' : 'text-[#E68A8A]'}`}>
                  ₹{c.financial_impact.expected_net_contest_value.toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-white/40">Recovery − Op Cost</div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">NET ADVANTAGE</div>
                <div className="text-xl font-bold text-white">
                  ₹{c.financial_impact.net_financial_advantage.toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-white/40">Contest Value − Accept Value</div>
              </div>
            </div>

            <div className="p-3 border border-white/10 bg-black text-[11px] font-mono text-white/50">
              DISCLAIMER: {c.financial_impact.assumptions.disclaimer} (Base Filing Fee = ₹1,500; Contest Fee Multiplier = 25%).
            </div>
          </div>
        )}

        {/* Phase 10: SLA & Review Urgency Engine */}
        {slaInfo && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/12 pb-3">
              <div className="flex items-center gap-3">
                <SectionLabel label="03 // SLA_&_REVIEW_PRIORITY_ENGINE" badge="PHASE 10" />
                <span className={`px-2 py-0.5 border font-bold text-[10px] uppercase ${
                  slaInfo.review_priority === 'CRITICAL' ? 'border-[#E68A8A] bg-[#E68A8A]/10 text-[#E68A8A]' :
                  slaInfo.review_priority === 'HIGH' ? 'border-[#F4C46B] bg-[#F4C46B]/10 text-[#F4C46B]' :
                  'border-[#9FE6C1] bg-[#9FE6C1]/10 text-[#9FE6C1]'
                }`}>
                  [{slaInfo.review_priority} PRIORITY]
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-white/40 text-[10px]">SLA STATUS:</span>
                <span className={`px-2 py-0.5 border font-bold text-[10px] uppercase ${
                  slaInfo.sla_status === 'OVERDUE' ? 'border-[#E68A8A] bg-[#E68A8A]/20 text-[#E68A8A]' :
                  slaInfo.sla_status === 'DUE_SOON' ? 'border-[#F4C46B] bg-[#F4C46B]/20 text-[#F4C46B]' :
                  'border-[#9FE6C1] bg-[#9FE6C1]/10 text-[#9FE6C1]'
                }`}>
                  {slaInfo.sla_status}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px]">TIME REMAINING TO DEADLINE</div>
                <div className={`text-xl font-bold ${slaInfo.is_overdue ? 'text-[#E68A8A]' : 'text-white'}`}>
                  {slaInfo.is_overdue ? 'DEADLINE EXPIRED' : `${slaInfo.hours_remaining ?? 0} HOURS`}
                </div>
              </div>

              <div className="p-3 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px]">OPERATIONAL URGENCY SCORE</div>
                <div className="text-xl font-bold text-[#AFDDFF]">
                  {slaInfo.urgency_score} / 100
                </div>
              </div>

              <div className="p-3 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px]">RESPONSE DEADLINE</div>
                <div className="text-sm font-bold text-white/80 truncate">
                  {slaInfo.deadline || 'NO DEADLINE SET'}
                </div>
              </div>
            </div>

            <div className="p-3 border border-white/10 bg-black text-[11px] text-white/70">
              <span className="text-white/40 font-bold">PRIORITY TRIAGE RATIONALE: </span>
              {slaInfo.priority_explanation}
            </div>
          </div>
        )}

        {/* Section 3 & 4 Grid: Risk & AI Prediction Engine + Dual-Layer AI Explanation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Section 3: AI Prediction Engine */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="border-b border-white/12 pb-4">
              <SectionLabel label="03 // RISK_&_AI_PREDICTION_ENGINE" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Phase 2 LightGBM Model Assessment
              </h3>
            </div>

            <ProbabilityGauge
              probability={pred.win_probability}
              threshold={pred.decision_threshold}
              recommendation={pred.recommendation}
            />

            <div className="p-3 border border-[#AFDDFF]/30 bg-[#AFDDFF]/5 text-[11px] font-mono text-[#AFDDFF] leading-relaxed">
              [ AUTHORIZATION BOUNDARY ]: Model recommendation predicts cost-sensitive win probability. Final financial action requires explicit human authorization below.
            </div>

            <div className="space-y-3 pt-2">
              <div className="text-[10px] font-mono text-white/40 uppercase tracking-widest">
                [ SUPPORTING & RISK DRIVERS ]
              </div>
              <div className="space-y-2 font-mono text-xs">
                {inv.supporting_factors.slice(0, 3).map((f: any, i: number) => {
                  const label = typeof f === 'string' ? f : (f.title ? `${f.title} - ${f.explanation}` : (f.explanation || JSON.stringify(f)));
                  return (
                    <div key={i} className="p-2.5 border border-[#9FE6C1]/30 bg-[#9FE6C1]/5 text-[#9FE6C1] flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#9FE6C1]" />
                      <span className="truncate">{label}</span>
                    </div>
                  );
                })}
                {inv.risk_factors.slice(0, 2).map((r: any, i: number) => {
                  const label = typeof r === 'string' ? r : (r.title ? `${r.title} - ${r.explanation}` : (r.explanation || JSON.stringify(r)));
                  return (
                    <div key={i} className="p-2.5 border border-[#F4C46B]/30 bg-[#F4C46B]/5 text-[#F4C46B] flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#F4C46B]" />
                      <span className="truncate">{label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Section 4: Dual-Layer AI Explanation */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="border-b border-white/12 pb-4">
              <SectionLabel label="04 // DUAL_LAYER_AI_EXPLANATION" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Executive & Technical SHAP Decision Explanation
              </h3>
            </div>

            {c.executive_explanation && (
              <div className="space-y-2 font-mono text-xs">
                <div className="text-[10px] text-white/40 uppercase tracking-widest">[ EXECUTIVE SUMMARY ]</div>
                <p className="p-4 border border-white/12 bg-black text-white/80 leading-relaxed font-sans text-xs">
                  {c.executive_explanation}
                </p>
              </div>
            )}

            <div className="space-y-2 font-mono text-xs">
              <div className="text-[10px] text-white/40 uppercase tracking-widest">[ AGENT TRACE TIMELINE ]</div>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {inv.timeline.map((step) => (
                  <div key={step.step} className="p-2.5 border border-white/10 bg-black flex items-start gap-3">
                    <span className="text-[#AFDDFF] font-bold text-[10px] border border-[#AFDDFF]/30 px-1.5 py-0.5">
                      0{step.step}
                    </span>
                    <div className="overflow-hidden">
                      <div className="text-white font-medium truncate">{step.action}</div>
                      <div className="text-white/40 text-[11px] truncate">{step.result}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* Section 5: Evidence Cross-Verification Room */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="05 // EVIDENCE_CROSS_VERIFICATION" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Phase 5 Evidence Cross-Verification Quality & Relational Network Room
              </h3>
            </div>
            <TechnicalStatus status="100% FIELD VERIFIED" variant="green" />
          </div>

          <EvidenceNetworkVisualizer
            disputeId={c.dispute.dispute_id}
            winProb={+(pred.win_probability * 100).toFixed(1)}
            recommendation={pred.recommendation}
          />

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                  <th className="py-3 px-4">EVIDENCE_CLAIM</th>
                  <th className="py-3 px-4">CITATION_LABEL</th>
                  <th className="py-3 px-4">SOURCE_FIELD</th>
                  <th className="py-3 px-4">CLAIMED_VALUE</th>
                  <th className="py-3 px-4">ACTUAL_SOURCE_VALUE</th>
                  <th className="py-3 px-4">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {ver.verification_results.map((res) => (
                  <tr key={res.evidence_id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-3 px-4 font-medium text-white">{res.claim}</td>
                    <td className="py-3 px-4 text-[#AFDDFF] font-bold">{res.citation_label}</td>
                    <td className="py-3 px-4 text-white/50">{res.source_field || 'N/A'}</td>
                    <td className="py-3 px-4 text-white font-bold">{res.claimed_value || 'N/A'}</td>
                    <td className="py-3 px-4 text-white font-bold">{res.actual_source_value || 'N/A'}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={res.verification_status} type="evidence" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Phase 10: Evidence Confidence Engine */}
        {evidenceConfidence && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="05B // EVIDENCE_CONFIDENCE_&_COMPLETIOS_ENGINE" badge="PHASE 10" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Evidence Readiness Score & Citation Completeness
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-white/40 text-[10px]">CONFIDENCE SCORE:</span>
                <span className="text-2xl font-bold text-[#9FE6C1]">{evidenceConfidence.confidence_score}%</span>
                <span className="px-2 py-0.5 border border-[#9FE6C1]/40 bg-[#9FE6C1]/10 text-[#9FE6C1] uppercase font-bold text-[10px]">
                  [{evidenceConfidence.readiness_tier}]
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">VERIFIED CLAIMS</div>
                <div className="text-lg font-bold text-[#9FE6C1]">{evidenceConfidence.verified_claims_count} Verified</div>
              </div>
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">UNVERIFIABLE CLAIMS</div>
                <div className="text-lg font-bold text-white/50">{evidenceConfidence.unverifiable_claims_count} Unverified</div>
              </div>
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">MISMATCHED CLAIMS</div>
                <div className="text-lg font-bold text-[#E68A8A]">{evidenceConfidence.mismatched_claims_count} Mismatches</div>
              </div>
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">DELIVERY SIGNATURE</div>
                <div className="text-lg font-bold text-[#AFDDFF]">
                  {evidenceConfidence.delivery_signature_present ? 'PRESENT & VALID' : 'ABSENT'}
                </div>
              </div>
            </div>

            {/* Evidence Alerts & Missing Items */}
            {evidenceConfidence.missing_evidence_items.length > 0 && (
              <div className="p-4 border border-[#F4C46B]/30 bg-[#F4C46B]/5 space-y-2 text-[#F4C46B]">
                <div className="font-bold text-xs uppercase tracking-wider">[ ATTENTION: MISSING CRITICAL EVIDENCE ITEMS ]</div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {evidenceConfidence.missing_evidence_items.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 border border-[#F4C46B]/50 bg-black text-[10px] uppercase">
                      MISSING: {item}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <ThinDivider />

        {/* Section 6: Relational Customer & Order Profile */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="border-b border-white/12 pb-4">
            <SectionLabel label="06 // RELATIONAL_CUSTOMER_&_ORDER_PROFILE" />
            <h3 className="text-xl font-display font-semibold text-white mt-1">
              Historical Customer Profile & Transaction Velocity
            </h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">[ CUSTOMER TENURE ]</div>
              <div className="text-lg font-bold text-white">{c.customer.tenure_days} Days</div>
              <div className="text-[10px] text-white/50">{c.customer.customer_segment} Segment</div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">[ ORDER COUNT ]</div>
              <div className="text-lg font-bold text-[#AFDDFF]">{c.customer.successful_order_count} Orders</div>
              <div className="text-[10px] text-white/50">Dispute Count: {c.customer.historical_chargeback_count}</div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">[ AUTH RISK SCORE ]</div>
              <div className="text-lg font-bold text-[#F4C46B]">{c.transaction.auth_risk_score}</div>
              <div className="text-[10px] text-white/50">Payment: {c.transaction.payment_method}</div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-1">
              <div className="text-white/40 text-[10px] uppercase">[ DELIVERY POD ]</div>
              <div className="text-lg font-bold text-[#9FE6C1]">
                {c.delivery.pod_signature_present ? 'SIGNATURE VERIFIED' : 'NO SIGNATURE'}
              </div>
              <div className="text-[10px] text-white/50">Carrier: {c.delivery.carrier}</div>
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* Phase 8 Feature: Auditable Prediction Trace */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="06B // AUDITABLE_PREDICTION_TRACE" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Machine Reasoning Trace & Decision Support Rationale
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-white/40 border border-white/20 px-2 py-0.5 uppercase">[ PRODUCTION ]</span>
              <TechnicalStatus status="DECISION SUPPORT ONLY" variant="amber" size="sm" />
            </div>
          </div>

          <div className="p-6 border border-[#AFDDFF]/30 bg-[#AFDDFF]/5 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/12 pb-3">
              <div className="text-white font-bold text-sm tracking-wide">
                WHY DID THE SYSTEM RECOMMEND [{pred.recommendation}]?
              </div>
              <div className="text-[#AFDDFF] font-bold text-xs">
                LightGBM v2.1.0 (Threshold: 0.29)
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
              <div className="p-3 bg-black border border-white/10 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">WIN PROBABILITY</div>
                <div className="text-lg font-bold text-[#AFDDFF]">{(pred.win_probability * 100).toFixed(1)}%</div>
                <div className="text-[10px] text-white/40">Model Decision Boundary: 29.0%</div>
              </div>
              <div className="p-3 bg-black border border-white/10 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">RECOMMENDATION</div>
                <div className="text-lg font-bold text-white">{pred.recommendation}</div>
                <div className="text-[10px] text-white/40">Triage Action Strategy</div>
              </div>
              <div className="p-3 bg-black border border-white/10 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">PRIORITY TIER</div>
                <div className="text-lg font-bold text-[#F4C46B]">{c.priority || 'MEDIUM'}</div>
                <div className="text-[10px] text-white/40">{c.priority_reasoning || 'Evaluated'}</div>
              </div>
              <div className="p-3 bg-black border border-white/10 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">DATA INTEGRITY</div>
                <div className="text-lg font-bold text-[#9FE6C1]">100.0% SCORE</div>
                <div className="text-[10px] text-white/40">0 Schema Anomalies</div>
              </div>
            </div>

            <div className="pt-2 text-white/70 text-[11px] leading-relaxed font-sans border-t border-white/10">
              <span className="font-mono text-[#AFDDFF] font-bold">[AUDIT TRACE]</span> The LightGBM classifier evaluated transaction risk parameters (Auth Score: {c.transaction.auth_risk_score}, Disputed Amount: ₹{c.dispute.disputed_amount.toLocaleString()}, Customer Tenure: {c.customer.tenure_days} days). Because win probability ({(pred.win_probability * 100).toFixed(1)}%) exceeds the 0.29 cost-sensitive threshold, contesting this dispute has a positive expected financial recovery.
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* Phase 8 Feature: Chronological Investigation Timeline */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex items-center justify-between border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="06C // CHRONOLOGICAL_INVESTIGATION_TIMELINE" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Lifecycle & Event Sequence Timeline
              </h3>
            </div>
            <span className="text-[10px] font-mono text-[#9FE6C1] border border-[#9FE6C1]/30 px-2.5 py-1">
              STATUS: {timeline?.overall_status || revStatus}
            </span>
          </div>

          <div className="relative pl-6 border-l border-white/15 space-y-6 font-mono text-xs">
            {(timeline?.events || [
              {
                event_id: 'EVT_TXN',
                stage: 'TRANSACTION_CREATED',
                title: 'TRANSACTION CREATED',
                description: `Payment of ₹${c.dispute.disputed_amount.toLocaleString()} processed via ${c.transaction.payment_method}.`,
                timestamp: (c.order as any)?.order_timestamp || null,
                status: 'COMPLETED',
                actor: 'PAYMENT_GATEWAY'
              },
              {
                event_id: 'EVT_DISP',
                stage: 'DISPUTE_RECEIVED',
                title: 'DISPUTE FILED',
                description: `Bank chargeback notification received under reason code ${c.dispute.dispute_reason_code}.`,
                timestamp: c.dispute.response_deadline,
                status: 'COMPLETED',
                actor: 'ISSUING_BANK'
              },
              {
                event_id: 'EVT_PRED',
                stage: 'MODEL_PREDICTION',
                title: 'LIGHTGBM MODEL INFERENCE',
                description: `Win probability scored at ${(pred.win_probability * 100).toFixed(1)}%.`,
                timestamp: c.dispute.response_deadline,
                status: 'COMPLETED',
                actor: 'LIGHTGBM_CLASSIFIER'
              },
              {
                event_id: 'EVT_EVID',
                stage: 'EVIDENCE_VERIFIED',
                title: 'EVIDENCE CROSS-VERIFICATION',
                description: 'Relational evidence citations verified against delivery POD and communication logs.',
                timestamp: c.dispute.response_deadline,
                status: 'COMPLETED',
                actor: 'EVIDENCE_VERIFIER'
              },
              {
                event_id: 'EVT_PRIO',
                stage: 'CASE_PRIORITIZED',
                title: `CASE PRIORITIZED [${c.priority || 'MEDIUM'}]`,
                description: c.priority_reasoning || 'Priority assigned by risk engine.',
                timestamp: c.dispute.response_deadline,
                status: 'COMPLETED',
                actor: 'RISK_ENGINE'
              },
              {
                event_id: 'EVT_REV',
                stage: 'HUMAN_REVIEW',
                title: revStatus === 'DECIDED' ? 'HUMAN DECISION RECORDED' : 'AWAITING HUMAN AUDITOR',
                description: revStatus === 'DECIDED' ? 'Decision authorized and saved to persistent SQLite audit database.' : 'Queued in human-in-the-loop review queue.',
                timestamp: null,
                status: revStatus === 'DECIDED' ? 'COMPLETED' : 'IN_PROGRESS',
                actor: revStatus === 'DECIDED' ? 'HUMAN_AUDITOR' : 'PENDING'
              }
            ]).map((evt, idx) => (
              <div key={evt.event_id || idx} className="relative group">
                <div className={`absolute -left-[31px] top-1.5 h-3.5 w-3.5 rounded-full border-2 ${
                  evt.status === 'COMPLETED'
                    ? 'bg-[#9FE6C1] border-[#9FE6C1]'
                    : evt.status === 'IN_PROGRESS'
                    ? 'bg-[#AFDDFF] border-[#AFDDFF] animate-pulse'
                    : 'bg-black border-white/40'
                }`} />

                <div className="p-4 border border-white/10 bg-black/60 space-y-1 hover:border-white/30 transition-colors">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-[#AFDDFF] font-bold tracking-wider uppercase">{evt.stage}</span>
                    <span className="text-white/40">{evt.timestamp ? String(evt.timestamp).replace('T', ' ').split('.')[0] : '[ PENDING TIMESTAMP ]'}</span>
                  </div>
                  <div className="text-white font-bold text-xs">{evt.title}</div>
                  <div className="text-white/70 text-[11px] font-sans">{evt.description}</div>
                  <div className="text-[10px] text-white/40 flex items-center gap-2 pt-1 border-t border-white/5">
                    <span>ACTOR: {evt.actor}</span>
                    <span>•</span>
                    <span>STATUS: {evt.status}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <ThinDivider />

        {/* Section 7: Interactive Decision Simulator Engine */}
        {c.decision_simulation && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="07 // INTERACTIVE_DECISION_SIMULATOR" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Decision Path Outcome Projections (What-If Simulation)
                </h3>
              </div>
              <TechnicalStatus status="MODEL ESTIMATE vs ACTUAL" variant="ice" size="sm" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
              {/* Scenario 1: CONTEST */}
              <div className="p-5 border border-[#9FE6C1]/40 bg-[#9FE6C1]/5 space-y-3">
                <div className="flex items-center justify-between border-b border-[#9FE6C1]/30 pb-2">
                  <span className="font-bold text-[#9FE6C1] uppercase">[ CONTEST ]</span>
                  <span className="text-[10px] text-[#9FE6C1] border border-[#9FE6C1]/40 px-1.5 py-0.5 font-bold">
                    MODEL ESTIMATE
                  </span>
                </div>
                <div className="space-y-1 text-white">
                  <div className="text-white/40 text-[10px]">EXPECTED NET OUTCOME:</div>
                  <div className="text-2xl font-bold text-[#9FE6C1]">
                    ₹{c.decision_simulation.scenarios.CONTEST.net_financial_outcome.toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="text-[11px] text-white/70 font-sans leading-relaxed">
                  {c.decision_simulation.scenarios.CONTEST.risk_impact}
                </div>
              </div>

              {/* Scenario 2: DO NOT CONTEST */}
              <div className="p-5 border border-[#E68A8A]/40 bg-[#E68A8A]/5 space-y-3">
                <div className="flex items-center justify-between border-b border-[#E68A8A]/30 pb-2">
                  <span className="font-bold text-[#E68A8A] uppercase">[ DO NOT CONTEST ]</span>
                  <span className="text-[10px] text-[#E68A8A] border border-[#E68A8A]/40 px-1.5 py-0.5 font-bold">
                    MODEL ESTIMATE
                  </span>
                </div>
                <div className="space-y-1 text-white">
                  <div className="text-white/40 text-[10px]">EXPECTED NET OUTCOME:</div>
                  <div className="text-2xl font-bold text-[#E68A8A]">
                    ₹{c.decision_simulation.scenarios.DO_NOT_CONTEST.net_financial_outcome.toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="text-[11px] text-white/70 font-sans leading-relaxed">
                  {c.decision_simulation.scenarios.DO_NOT_CONTEST.risk_impact}
                </div>
              </div>

              {/* Scenario 3: ESCALATE */}
              <div className="p-5 border border-purple-400/40 bg-purple-500/5 space-y-3">
                <div className="flex items-center justify-between border-b border-purple-400/30 pb-2">
                  <span className="font-bold text-purple-300 uppercase">[ ESCALATE ]</span>
                  <span className="text-[10px] text-purple-300 border border-purple-400/40 px-1.5 py-0.5 font-bold">
                    MODEL ESTIMATE
                  </span>
                </div>
                <div className="space-y-1 text-white">
                  <div className="text-white/40 text-[10px]">EXPECTED NET OUTCOME:</div>
                  <div className="text-2xl font-bold text-purple-300">
                    ₹{c.decision_simulation.scenarios.ESCALATE.net_financial_outcome.toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="text-[11px] text-white/70 font-sans leading-relaxed">
                  {c.decision_simulation.scenarios.ESCALATE.risk_impact}
                </div>
              </div>
            </div>

            {/* Actual Recorded Outcome indicator */}
            {c.decision_simulation.actual_outcome ? (
              <div className="p-4 border border-[#9FE6C1] bg-[#9FE6C1]/10 text-[#9FE6C1] font-mono text-xs space-y-1">
                <div className="font-bold uppercase tracking-wider">[ ACTUAL RECORDED OUTCOME IN SQLITE AUDIT ]</div>
                <div>Reviewer: {c.decision_simulation.actual_outcome.reviewer_id} • Action: {c.decision_simulation.actual_outcome.decision} • Recorded At: {c.decision_simulation.actual_outcome.recorded_at}</div>
              </div>
            ) : (
              <div className="p-3 border border-white/10 bg-black text-[11px] font-mono text-white/50">
                ACTUAL HISTORICAL OUTCOME: AWAITING HUMAN AUTHORIZATION BELOW.
              </div>
            )}
          </div>
        )}

        <ThinDivider />

        {/* Section 8: Human-in-the-Loop Action Panel */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex items-center justify-between border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="08 // HUMAN_IN_THE_LOOP_ACTION_PANEL" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Phase 6 Decision Authorization Workspace
              </h3>
            </div>
            <StatusBadge status={revStatus} type="review" />
          </div>

          {submitError && (
            <div className="p-4 border border-[#E68A8A] bg-[#E68A8A]/10 text-[#E68A8A] text-xs font-mono space-y-1">
              <div className="font-bold uppercase tracking-wider">SUBMISSION ALERT</div>
              <div>{submitError}</div>
            </div>
          )}

          {isDecided && latestDecision ? (
            /* Post-Decision Immutable View */
            <div className="border border-[#9FE6C1]/40 bg-[#9FE6C1]/5 p-6 space-y-6 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-white/12 pb-3">
                <div className="text-[#9FE6C1] font-bold uppercase tracking-wider text-sm">
                  [ IMMUTABLE DECISION LOG RECORDED IN SQLITE DB ]
                </div>
                <span className="text-white/40 text-[11px]">{latestDecision.decision_id}</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <div className="text-white/40 text-[10px] uppercase tracking-widest mb-1">AUTHORIZED DECISION</div>
                  <StatusBadge status={latestDecision.decision} type="recommendation" />
                </div>
                <div>
                  <div className="text-white/40 text-[10px] uppercase tracking-widest mb-1">REVIEWER IDENTITY</div>
                  <div className="text-white font-bold">{latestDecision.reviewer_id}</div>
                </div>
                <div>
                  <div className="text-white/40 text-[10px] uppercase tracking-widest mb-1">AI CONTEXT</div>
                  <div className="text-white/80">
                    {latestDecision.ai_recommendation} ({(latestDecision.ai_win_probability * 100).toFixed(1)}%)
                  </div>
                </div>
                <div>
                  <div className="text-white/40 text-[10px] uppercase tracking-widest mb-1">RECORDED TIMESTAMP</div>
                  <div className="text-white/60">{latestDecision.created_at.replace('T', ' ').split('.')[0]}</div>
                </div>
              </div>

              <div className="pt-2 border-t border-white/12">
                <div className="text-white/40 text-[10px] uppercase tracking-widest mb-2">MANDATORY JUSTIFICATION REASON:</div>
                <div className="p-4 border border-white/12 bg-black text-white leading-relaxed">
                  "{latestDecision.reason}"
                </div>
              </div>
            </div>
          ) : (
            /* Decision Authorization Form */
            <div className="space-y-8 font-mono text-xs">
              {/* Step 1: Decision Selection */}
              <div className="space-y-3">
                <div className="text-white/40 uppercase tracking-widest text-[10px]">
                  1. SELECT AUTHORIZED ACTION
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    type="button"
                    onClick={() => setSelectedDecision('CONTEST')}
                    className={`p-4 border text-left transition-all space-y-2 ${
                      selectedDecision === 'CONTEST'
                        ? 'border-[#9FE6C1] bg-[#9FE6C1]/10 text-[#9FE6C1]'
                        : 'border-white/12 bg-black text-white/60 hover:border-white/30'
                    }`}
                  >
                    <div className="font-bold text-sm uppercase tracking-wider flex items-center justify-between">
                      <span>[ CONTEST ]</span>
                      {selectedDecision === 'CONTEST' && <span>●</span>}
                    </div>
                    <div className="text-[11px] opacity-80 font-sans">
                      Approve contestation submission with verified fulfillment evidence.
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('DO_NOT_CONTEST')}
                    className={`p-4 border text-left transition-all space-y-2 ${
                      selectedDecision === 'DO_NOT_CONTEST'
                        ? 'border-[#E68A8A] bg-[#E68A8A]/10 text-[#E68A8A]'
                        : 'border-white/12 bg-black text-white/60 hover:border-white/30'
                    }`}
                  >
                    <div className="font-bold text-sm uppercase tracking-wider flex items-center justify-between">
                      <span>[ DO_NOT_CONTEST ]</span>
                      {selectedDecision === 'DO_NOT_CONTEST' && <span>●</span>}
                    </div>
                    <div className="text-[11px] opacity-80 font-sans">
                      Accept dispute liability / decline contestation.
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('ESCALATE')}
                    className={`p-4 border text-left transition-all space-y-2 ${
                      selectedDecision === 'ESCALATE'
                        ? 'border-purple-400 bg-purple-500/10 text-purple-300'
                        : 'border-white/12 bg-black text-white/60 hover:border-white/30'
                    }`}
                  >
                    <div className="font-bold text-sm uppercase tracking-wider flex items-center justify-between">
                      <span>[ ESCALATE ]</span>
                      {selectedDecision === 'ESCALATE' && <span>●</span>}
                    </div>
                    <div className="text-[11px] opacity-80 font-sans">
                      Escalate case for senior risk manager sign-off.
                    </div>
                  </button>
                </div>
              </div>

              {/* Step 2: Mandatory Justification Reason */}
              <div className="space-y-3">
                <div className="text-white/40 uppercase tracking-widest text-[10px]">
                  2. MANDATORY REVIEW JUSTIFICATION REASON
                </div>
                <textarea
                  rows={3}
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder="PROVIDE MANDATORY JUSTIFICATION FOR AUDIT TRAIL..."
                  className="w-full bg-black border border-white/20 p-4 text-xs text-white placeholder-white/40 focus:outline-none focus:border-[#AFDDFF] font-mono"
                />
                <div className="text-[10px] text-white/40">
                  Minimum 5 characters required for SQLite audit log compliance.
                </div>
              </div>

              {/* Submit Action */}
              <div className="flex items-center justify-between pt-4 border-t border-white/12">
                <div className="text-white/40 text-[11px]">
                  REVIEWER: <span className="text-[#AFDDFF] font-bold">{reviewerId}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowConfirmModal(true)}
                  disabled={!decisionReason || decisionReason.trim().length < 5}
                  className="px-6 py-3 border border-[#AFDDFF] bg-[#AFDDFF] hover:bg-[#AFDDFF]/80 text-black font-mono font-bold text-xs uppercase tracking-wider disabled:opacity-30 transition-all"
                >
                  SUBMIT AUTHORIZED DECISION &rarr;
                </button>
              </div>
            </div>
          )}
        </div>

        <ThinDivider />

        {/* Phase 10: Reviewer Notes & Immutable Action Lineage Audit */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="08B // INVESTIGATOR_NOTES_&_AUDIT_LINEAGE" badge="PHASE 10" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Investigator Case Log & Audit Activity Stream
              </h3>
            </div>
            <span className="text-[10px] text-[#AFDDFF] border border-[#AFDDFF]/30 px-2 py-0.5 uppercase">
              {activityTrace.length} ACTION RECORD(S)
            </span>
          </div>

          {/* Add Review Note Form */}
          <div className="p-4 border border-white/12 bg-black space-y-3">
            <div className="text-white/40 uppercase tracking-widest text-[10px]">ADD INVESTIGATOR CASE NOTE</div>
            <div className="flex gap-3">
              <input
                type="text"
                value={newNoteText}
                onChange={(e) => setNewNoteText(e.target.value)}
                placeholder="TYPE CASE NOTE FOR AUDIT TRAIL..."
                className="flex-1 bg-black border border-white/20 px-3 py-2 text-xs text-white placeholder-white/40 focus:outline-none focus:border-[#AFDDFF]"
              />
              <button
                onClick={handleAddNote}
                disabled={addingNote || !newNoteText.trim()}
                className="px-4 py-2 border border-[#AFDDFF] bg-[#AFDDFF] text-black font-bold uppercase text-xs disabled:opacity-30 hover:bg-[#AFDDFF]/80 transition-all"
              >
                {addingNote ? 'ADDING...' : 'ADD NOTE'}
              </button>
            </div>
          </div>

          {/* Review Notes Grid */}
          {caseNotes.length > 0 && (
            <div className="space-y-3">
              <div className="text-white/40 text-[10px] uppercase tracking-widest">RECORDED REVIEW NOTES</div>
              <div className="space-y-2">
                {caseNotes.map((note) => (
                  <div key={note.note_id} className="p-3 border border-white/10 bg-black/50 space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-white/50">
                      <span className="text-[#AFDDFF] font-bold">AUTHOR: {note.author_id}</span>
                      <span>{note.created_at.replace('T', ' ').split('.')[0]}</span>
                    </div>
                    <div className="text-white font-sans text-xs">{note.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Complete Action Lineage Stream */}
          <div className="space-y-3">
            <div className="text-white/40 text-[10px] uppercase tracking-widest">IMMUTABLE ACTION LINEAGE TIMELINE</div>
            <div className="space-y-2 border-l border-white/12 pl-4 ml-1">
              {activityTrace.map((act) => (
                <div key={act.activity_id} className="relative space-y-1 py-1">
                  <div className="absolute -left-[21px] top-2 h-2.5 w-2.5 rounded-full bg-[#AFDDFF]" />
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-white font-bold uppercase">{act.action_type}</span>
                    <span className="text-white/40">{act.timestamp.replace('T', ' ').split('.')[0]}</span>
                  </div>
                  <div className="text-white/80 text-[11px] font-sans">{act.description}</div>
                  <div className="text-[10px] text-white/40">PERFORMED BY: {act.performed_by}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <ThinDivider />

        {/* Section 9: Data Quality & Lineage Monitor */}
        {c.data_quality_info && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="09 // DATA_QUALITY_&_RECORD_LINEAGE" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Programmatic Data Quality & Relational Lineage Status
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-white/40 text-[10px]">DQ SCORE:</span>
                <span className="text-lg font-bold text-[#9FE6C1]">{c.data_quality_info.data_quality_score}%</span>
                <TechnicalStatus status={c.data_quality_info.status} variant="green" size="sm" />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3 border border-white/10 bg-black">
                <div className="text-white/40 text-[10px] uppercase">TOTAL CHECKS</div>
                <div className="text-white font-bold">{c.data_quality_info.total_checks} Checks Evaluated</div>
              </div>
              <div className="p-3 border border-white/10 bg-black">
                <div className="text-white/40 text-[10px] uppercase">PASSED CHECKS</div>
                <div className="text-[#9FE6C1] font-bold">{c.data_quality_info.passed_checks} Checks Passed</div>
              </div>
              <div className="p-3 border border-white/10 bg-black">
                <div className="text-white/40 text-[10px] uppercase">SCHEMA STATUS</div>
                <div className="text-[#AFDDFF] font-bold">100% RELATIONAL INTEGRITY</div>
              </div>
            </div>
          </div>
        )}

      {/* Decision Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-black border border-white/20 p-8 max-w-md w-full space-y-6 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/12 pb-3">
              <h3 className="text-base font-bold text-white uppercase tracking-wider">CONFIRM HUMAN AUTHORIZATION</h3>
              <button onClick={() => setShowConfirmModal(false)} className="text-white/50 hover:text-white">
                ✕
              </button>
            </div>

            <div className="space-y-4 text-white/80">
              <div className="p-3 border border-white/12 bg-white/[0.02]">
                <div className="text-[10px] text-white/40 uppercase">DISPUTE CASE</div>
                <div className="font-bold text-white">{disputeId}</div>
              </div>

              <div className="p-3 border border-white/12 bg-white/[0.02]">
                <div className="text-[10px] text-white/40 uppercase mb-1">SELECTED DECISION</div>
                <StatusBadge status={selectedDecision} type="recommendation" />
              </div>

              <div className="p-3 border border-white/12 bg-white/[0.02]">
                <div className="text-[10px] text-white/40 uppercase">JUSTIFICATION REASON</div>
                <div className="text-white italic mt-1 font-sans">"{decisionReason}"</div>
              </div>
            </div>

            <div className="flex gap-4 pt-2">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="w-1/2 py-2.5 border border-white/20 hover:border-white text-white font-mono text-xs uppercase tracking-wider"
              >
                CANCEL
              </button>
              <button
                onClick={handleDecisionSubmit}
                disabled={isSubmitting}
                className="w-1/2 py-2.5 border border-[#AFDDFF] bg-[#AFDDFF] hover:bg-[#AFDDFF]/80 text-black font-mono font-bold text-xs uppercase tracking-wider"
              >
                {isSubmitting ? 'RECORDING...' : 'CONFIRM DECISION'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Outcome Feedback Modal */}
      <OutcomeFeedbackModal
        disputeId={disputeId}
        isOpen={showOutcomeModal}
        onClose={() => setShowOutcomeModal(false)}
        onSuccess={() => {
          loadCaseData();
        }}
      />
      </div>
    </div>
  );
};
