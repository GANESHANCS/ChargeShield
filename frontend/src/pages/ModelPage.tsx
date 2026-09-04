import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  ModelPerformanceResponse,
  ModelMonitoringInfo,
  ModelFeedbackInfo,
  CalibrationResponse,
  ThresholdOptimizationResponse,
  ModelRegistryResponse,
  LearningMetricsResponse,
  ModelOutcomeRecord
} from '../types';
import { SectionLabel } from '../components/visual/SectionLabel';
import { MetricDisplay } from '../components/visual/MetricDisplay';
import { TechnicalStatus } from '../components/visual/TechnicalStatus';
import { ThinDivider } from '../components/visual/ThinDivider';
import { ModelPathVisualizer } from '../components/visual/ModelPathVisualizer';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { EditorialImageHero } from '../components/visual/EditorialImageHero';
import { ThresholdApprovalModal } from '../components/ThresholdApprovalModal';

import { useAuth } from '../context/AuthContext';

export const ModelPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const [modelPerf, setModelPerf] = useState<ModelPerformanceResponse | null>(null);
  const [monitoring, setMonitoring] = useState<ModelMonitoringInfo | null>(null);
  const [feedback, setFeedback] = useState<ModelFeedbackInfo | null>(null);

  // Phase 12 states
  const [calibration, setCalibration] = useState<CalibrationResponse | null>(null);
  const [thresholds, setThresholds] = useState<ThresholdOptimizationResponse | null>(null);
  const [registry, setRegistry] = useState<ModelRegistryResponse | null>(null);
  const [learning, setLearning] = useState<LearningMetricsResponse | null>(null);
  const [outcomes, setOutcomes] = useState<ModelOutcomeRecord[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Admin threshold modal state
  const [showThresholdModal, setShowThresholdModal] = useState(false);

  const fetchModelData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [perf, mon, fb, cal, thresh, reg, lr, out] = await Promise.all([
        api.getModelPerformance().catch(() => null),
        api.getModelMonitoring().catch(() => null),
        api.getModelFeedback().catch(() => null),
        api.getModelCalibration().catch(() => null),
        api.getModelThresholds().catch(() => null),
        api.getModelRegistry().catch(() => null),
        api.getContinuousLearning().catch(() => null),
        api.getDisputeOutcomes().catch(() => ({ outcomes: [] }))
      ]);

      if (perf) setModelPerf(perf);
      if (mon) setMonitoring(mon);
      if (fb) setFeedback(fb);
      if (cal) setCalibration(cal);
      if (thresh) setThresholds(thresh);
      if (reg) setRegistry(reg);
      if (lr) setLearning(lr);
      if (out && out.outcomes) setOutcomes(out.outcomes);

      if (!perf && !mon && !cal && !thresh) {
        setError('Model intelligence services currently initializing or data stream unavailable.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch model performance metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 md:p-12 flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-white/50 font-mono text-xs tracking-widest uppercase">
          <span className="h-2 w-2 bg-[#A78BFA] animate-ping" />
          <span>FETCHING PHASE 12 CONTINUOUS LEARNING & MODEL GOVERNANCE REPORT...</span>
        </div>
      </div>
    );
  }

  if (error && !modelPerf && !monitoring && !calibration) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 bg-[#E68A8A]/10 border border-[#E68A8A]/30 p-6 text-[#E68A8A] space-y-3 font-mono text-xs">
        <div className="font-bold text-sm uppercase tracking-wider">[ MODEL EVALUATION REPORT UNAVAILABLE ]</div>
        <p>{error}</p>
        <button
          onClick={fetchModelData}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-mono text-xs uppercase border border-white/20"
        >
          RETRY DATA FETCH
        </button>
      </div>
    );
  }

  // Safe defensive extraction to prevent ANY TypeError or black screen crashes
  const meta = modelPerf?.model_metadata || null;
  const rep = modelPerf?.evaluation_report || (modelPerf as any)?.evaluation_report_artifact || null;

  const lgbmOpt = rep?.primary_lightgbm_optimal_threshold?.metrics || null;
  const logReg = rep?.baseline_logistic_regression || null;
  const sim = rep?.financial_cost_simulation_inr || null;

  return (
    <div className="relative min-h-screen bg-transparent">
      <AnimatedBackground variant="model" />

      {/* Editorial Image Hero Header */}
      <EditorialImageHero
        imageSrc="/assets/model_math_boundary.png"
        category="04 / MODEL_GOVERNANCE_&_CONTINUOUS_LEARNING"
        titleLines={['MODEL INTELLIGENCE', '& GOVERNANCE']}
        subtitle="Production model monitoring, probability calibration, threshold optimization, outcome feedback & model registry."
        metadata={[
          { label: 'ACTIVE MODEL', value: registry?.active_production_model?.model_name || meta?.primary_algorithm || 'LightGBM Classifier' },
          { label: 'VERSION', value: registry?.active_production_model?.version_id || 'v1.0.0-prod' },
          { label: 'ACTIVE THRESHOLD', value: thresholds?.current_threshold !== undefined && thresholds?.current_threshold !== null ? `${thresholds.current_threshold}` : 'N/A' },
          { label: 'GOVERNANCE RULE', value: 'NO_AUTONOMOUS_RETRAINING' }
        ]}
      />

      <div className="relative z-10 px-[20px] md:px-[35px] py-12 space-y-12 max-w-[1600px] mx-auto animate-lumen-fade-up">

        {/* Phase 12 Section 1: Governance & Continuous Learning Readiness Card */}
        {learning && (
          <div className="border border-[#AFDDFF]/30 p-6 bg-[#AFDDFF]/5 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="01 // CONTINUOUS_LEARNING_&_GOVERNANCE" badge="PHASE 12" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Continuous Learning Pipeline & Non-Autonomous Guardrails
                </h3>
              </div>
              <TechnicalStatus
                status={`PIPELINE: ${learning?.pipeline_readiness?.status || 'MONITORING'}`}
                variant={learning?.pipeline_readiness?.status === 'READY' ? 'green' : 'amber'}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 font-mono text-xs">
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">HUMAN-AI AGREEMENT RATE</div>
                <div className="text-2xl font-bold text-[#9FE6C1]">
                  {learning?.human_ai_agreement_rate !== undefined && learning?.human_ai_agreement_rate !== null
                    ? `${(learning.human_ai_agreement_rate * 100).toFixed(1)}%`
                    : 'N/A'}
                </div>
                <div className="text-[10px] text-white/40">{learning?.agreement_status || 'MONITORING'}</div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">OUTCOME COVERAGE</div>
                <div className="text-2xl font-bold text-[#AFDDFF]">
                  {learning?.outcome_coverage?.coverage_percentage !== undefined && learning?.outcome_coverage?.coverage_percentage !== null
                    ? `${learning.outcome_coverage.coverage_percentage.toFixed(1)}%`
                    : 'N/A'}
                </div>
                <div className="text-[10px] text-white/40">
                  {learning?.outcome_coverage?.cases_with_ground_truth ?? 'N/A'} / {learning?.outcome_coverage?.total_production_predictions ?? 'N/A'} Cases Ground-Truthed
                </div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">LEARNING READINESS</div>
                <div className="text-xl font-bold text-[#F4C46B]">
                  {learning?.pipeline_readiness?.current_outcomes ?? 'N/A'} / {learning?.pipeline_readiness?.min_required_outcomes ?? 50}
                </div>
                <div className="text-[10px] text-white/40">Minimum 50 Ground-Truth Outcomes Required</div>
              </div>

              <div className="p-4 border border-purple-400/30 bg-purple-500/10 space-y-1">
                <div className="text-purple-300 text-[10px] uppercase font-bold">GOVERNANCE ENFORCEMENT</div>
                <div className="text-xs font-bold text-white uppercase">ENFORCED</div>
                <div className="text-[10px] text-purple-200/70">Autonomous Retraining Strictly Prohibited</div>
              </div>
            </div>

            <div className="p-3 border border-white/10 bg-black text-[11px] font-mono text-white/60 space-y-1">
              <div className="font-bold text-[#AFDDFF] uppercase">[ NON-NEGOTIABLE GOVERNANCE RULES ]</div>
              <ul className="list-disc pl-4 space-y-0.5 text-[10px] opacity-80">
                <li>Production ML models are never updated or retrained autonomously.</li>
                <li>Threshold changes require explicit Admin review, analytical justification, and audit authorization.</li>
                <li>Simulation cases are strictly isolated and barred from influencing production outcome feedback.</li>
              </ul>
            </div>
          </div>
        )}

        {/* Live Dual Algorithm Path Comparison Visualizer */}
        <ModelPathVisualizer />

        {/* Financial Cost Simulation Card */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="COST_SENSITIVE_SIMULATION" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Cost-Sensitive Financial Simulation (INR)
              </h3>
            </div>
            {sim?.cost_savings_inr !== undefined && sim?.cost_savings_inr !== null ? (
              <TechnicalStatus 
                status={`₹${sim.cost_savings_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })} SAVINGS`} 
                variant="green" 
              />
            ) : (
              <TechnicalStatus status="SIMULATION PENDING" variant="amber" />
            )}
          </div>

          {sim ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 font-mono text-xs">
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">NAIVE STRATEGY (ALWAYS CONTEST)</div>
                <div className="text-2xl font-light text-[#E68A8A]">
                  {sim.cost_naive_always_contest !== undefined ? `₹${sim.cost_naive_always_contest.toLocaleString('en-IN')}` : 'N/A'}
                </div>
                <div className="text-[10px] text-white/40">Incurs loss fees on weak cases</div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">MODEL @ DEFAULT (0.50 THRESHOLD)</div>
                <div className="text-2xl font-light text-[#F4C46B]">
                  {sim['cost_model_default_0.50'] !== undefined ? `₹${sim['cost_model_default_0.50'].toLocaleString('en-IN')}` : 'N/A'}
                </div>
                <div className="text-[10px] text-white/40">Standard classification threshold</div>
              </div>

              <div className="p-4 border border-[#AFDDFF]/40 bg-[#AFDDFF]/5 space-y-1">
                <div className="text-[#AFDDFF] text-[10px] uppercase font-bold">OPTIMAL MODEL @ 0.29 THRESHOLD</div>
                <div className="text-2xl font-light text-[#AFDDFF]">
                  {sim.cost_model_optimal_threshold !== undefined ? `₹${sim.cost_model_optimal_threshold.toLocaleString('en-IN')}` : 'N/A'}
                </div>
                <div className="text-[10px] text-[#AFDDFF]/80">Minimizes net financial loss</div>
              </div>

              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">NET FINANCIAL SAVINGS</div>
                <div className="text-2xl font-light text-[#9FE6C1]">
                  {sim.cost_savings_inr !== undefined ? `₹${sim.cost_savings_inr.toLocaleString('en-IN')}` : 'N/A'}
                </div>
                <div className="text-[10px] text-white/40">Over naive contestation strategy</div>
              </div>
            </div>
          ) : (
            <div className="p-6 border border-white/10 bg-black text-xs font-mono text-white/60">
              [ FINANCIAL COST SIMULATION DATA UNAVAILABLE ] — Simulation metrics have not been published by the backend evaluation engine.
            </div>
          )}
        </div>

        <ThinDivider />

        {/* Model Performance Comparison Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Primary LightGBM Model */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="PRIMARY_CLASSIFIER" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  {meta?.primary_algorithm || 'LightGBM Classifier'}
                </h3>
              </div>
              <TechnicalStatus status={lgbmOpt ? "SELECTED PRIMARY" : "UNAVAILABLE"} variant={lgbmOpt ? "green" : "amber"} size="sm" />
            </div>

            {lgbmOpt ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="ACCURACY" value={lgbmOpt.accuracy !== undefined ? `${(lgbmOpt.accuracy * 100).toFixed(2)}%` : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="PRECISION" value={lgbmOpt.precision !== undefined ? `${(lgbmOpt.precision * 100).toFixed(2)}%` : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="RECALL" value={lgbmOpt.recall !== undefined ? `${(lgbmOpt.recall * 100).toFixed(2)}%` : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="F1 SCORE" value={lgbmOpt.f1_score !== undefined ? lgbmOpt.f1_score.toFixed(4) : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="ROC-AUC" value={lgbmOpt.roc_auc !== undefined ? lgbmOpt.roc_auc.toFixed(4) : 'N/A'} accentColor="ice" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="PR-AUC" value={lgbmOpt.pr_auc !== undefined ? lgbmOpt.pr_auc.toFixed(4) : 'N/A'} accentColor="ice" />
                </div>
              </div>
            ) : (
              <div className="p-6 border border-white/10 bg-black text-xs font-mono text-white/60">
                [ PRIMARY CLASSIFIER EVALUATION METRICS UNAVAILABLE ]
              </div>
            )}
          </div>

          {/* Baseline Logistic Regression */}
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex items-center justify-between border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="BASELINE_BENCHMARK" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  {meta?.baseline_algorithm || 'Logistic Regression'}
                </h3>
              </div>
              <TechnicalStatus status={logReg ? "BASELINE" : "UNAVAILABLE"} variant={logReg ? "ice" : "amber"} size="sm" />
            </div>

            {logReg ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="ACCURACY" value={logReg.accuracy !== undefined ? `${(logReg.accuracy * 100).toFixed(2)}%` : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="PRECISION" value={logReg.precision !== undefined ? `${(logReg.precision * 100).toFixed(2)}%` : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="RECALL" value={logReg.recall !== undefined ? `${(logReg.recall * 100).toFixed(2)}%` : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="F1 SCORE" value={logReg.f1_score !== undefined ? logReg.f1_score.toFixed(4) : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="ROC-AUC" value={logReg.roc_auc !== undefined ? logReg.roc_auc.toFixed(4) : 'N/A'} accentColor="white" />
                </div>
                <div className="p-3 border border-white/12 bg-black">
                  <MetricDisplay label="PR-AUC" value={logReg.pr_auc !== undefined ? logReg.pr_auc.toFixed(4) : 'N/A'} accentColor="white" />
                </div>
              </div>
            ) : (
              <div className="p-6 border border-white/10 bg-black text-xs font-mono text-white/60">
                [ BASELINE BENCHMARK METRICS UNAVAILABLE ]
              </div>
            )}
          </div>
        </div>

        <ThinDivider />

        {/* Phase 12 Section 2: Model Calibration Curve Analysis */}
        {calibration && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="02 // PROBABILITY_CALIBRATION_ANALYSIS" badge="PHASE 12" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Probability Bucket Calibration & Expected Calibration Error (ECE)
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-white/40 uppercase">ECE: {(calibration.overall_expected_calibration_error * 100).toFixed(2)}%</span>
                <TechnicalStatus
                  status={calibration.calibration_status}
                  variant={calibration.calibration_status === 'CALIBRATED' ? 'green' : 'amber'}
                />
              </div>
            </div>

            {/* Probability Buckets Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-5 md:grid-cols-10 gap-2 font-mono text-xs">
              {calibration.buckets.map((b) => (
                <div key={b.bucket_range} className="p-2 border border-white/10 bg-black text-center space-y-1">
                  <div className="text-white/40 text-[9px] font-bold">{b.bucket_range}</div>
                  <div className="text-sm font-bold text-[#AFDDFF]">{b.predicted_count}</div>
                  <div className="text-[8px] text-white/30">Preds</div>
                  <div className="text-[9px] text-[#9FE6C1]">{(b.actual_win_rate * 100).toFixed(0)}%</div>
                  <div className="text-[8px] text-white/30">Win Rate</div>
                </div>
              ))}
            </div>

            <div className="p-3 border border-white/10 bg-black text-[11px] font-mono text-white/50">
              RECOMMENDATION: {calibration.recommendation} (Data Provenance: {calibration.data_provenance})
            </div>
          </div>
        )}

        <ThinDivider />

        {/* Phase 12 Section 3: Multi-Threshold Optimization & Admin Governance Approval */}
        {thresholds && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="03 // MULTI_THRESHOLD_OPTIMIZATION_&_GOVERNANCE" badge="PHASE 12" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Multi-Threshold Analytical Optimization & Admin Authorization
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-white/40 uppercase">ACTIVE: {thresholds.current_threshold}</span>
                {isAdmin ? (
                  <button
                    onClick={() => setShowThresholdModal(true)}
                    className="px-4 py-1.5 border border-[#A78BFA] bg-[#A78BFA]/20 text-[#A78BFA] font-bold hover:bg-[#A78BFA]/30 font-mono text-xs uppercase tracking-wider transition-all cursor-pointer"
                  >
                    APPROVE THRESHOLD CHANGE
                  </button>
                ) : (
                  <span className="px-3 py-1 border border-white/20 bg-white/5 text-white/50 text-[10px] font-mono uppercase tracking-wider">
                    [ ADMIN AUTHORIZATION REQUIRED ]
                  </span>
                )}
              </div>
            </div>

            {/* Threshold Evaluations Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                    <th className="py-3 px-4">THRESHOLD</th>
                    <th className="py-3 px-4">CONTEST / ACCEPT</th>
                    <th className="py-3 px-4">PRECISION</th>
                    <th className="py-3 px-4">RECALL</th>
                    <th className="py-3 px-4">F1 SCORE</th>
                    <th className="py-3 px-4">ACCURACY</th>
                    <th className="py-3 px-4">NET RECOVERY (INR)</th>
                    <th className="py-3 px-4">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {thresholds.threshold_evaluations.map((t) => {
                    const isCurrent = t.threshold === thresholds.current_threshold;
                    const isOptimalF1 = t.threshold === thresholds.optimal_f1_threshold;
                    const isOptimalFin = t.threshold === thresholds.optimal_financial_threshold;

                    return (
                      <tr
                        key={t.threshold}
                        className={`hover:bg-white/[0.03] ${
                          isCurrent ? 'bg-[#AFDDFF]/5 border-l-2 border-[#AFDDFF]' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-bold text-white text-sm">
                          {t.threshold.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-white/70">
                          {t.predicted_contest_count} / {t.predicted_accept_count}
                        </td>
                        <td className="py-3 px-4 text-white/70">{(t.precision * 100).toFixed(1)}%</td>
                        <td className="py-3 px-4 text-white/70">{(t.recall * 100).toFixed(1)}%</td>
                        <td className="py-3 px-4 text-white/90 font-bold">{t.f1_score.toFixed(4)}</td>
                        <td className="py-3 px-4 text-white/70">{(t.accuracy * 100).toFixed(1)}%</td>
                        <td className="py-3 px-4 text-[#9FE6C1] font-bold">
                          ₹{t.net_financial_recovery.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4">
                          {isCurrent && (
                            <span className="px-2 py-0.5 border border-[#AFDDFF] bg-[#AFDDFF]/20 text-[#AFDDFF] text-[9px] font-bold uppercase">
                              ACTIVE PROD
                            </span>
                          )}
                          {isOptimalFin && !isCurrent && (
                            <span className="px-2 py-0.5 border border-[#9FE6C1] bg-[#9FE6C1]/20 text-[#9FE6C1] text-[9px] font-bold uppercase">
                              FINANCIAL OPTIMAL
                            </span>
                          )}
                          {isOptimalF1 && !isCurrent && !isOptimalFin && (
                            <span className="px-2 py-0.5 border border-[#F4C46B] bg-[#F4C46B]/20 text-[#F4C46B] text-[9px] font-bold uppercase">
                              F1 OPTIMAL
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <ThinDivider />

        {/* Data Quality & Model Drift Foundation Panel */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="MODEL_MONITORING_&_DATA_QUALITY" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Data Quality Score & Drift Monitoring Foundation
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-white/40 border border-white/20 px-2 py-0.5 uppercase">[ {monitoring?.data_state_label || 'HISTORICAL / PRODUCTION'} ]</span>
              <TechnicalStatus status={`DRIFT: ${monitoring?.drift_status || 'AWAITING BASELINE'}`} variant="ice" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 font-mono text-xs">
            <div className="p-4 border border-white/12 bg-black space-y-2">
              <div className="text-white/40 text-[10px] uppercase">ACTIVE MODEL & VERSION</div>
              <div className="text-lg font-bold text-[#AFDDFF]">
                {monitoring?.current_model || 'LightGBM Classifier'} {monitoring?.model_version ? `v${monitoring.model_version}` : ''}
              </div>
              <div className="text-[10px] text-white/50">
                Optimal Cost Threshold: {monitoring?.threshold_in_use !== undefined && monitoring?.threshold_in_use !== null ? monitoring.threshold_in_use : 'N/A'}
              </div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-2">
              <div className="text-white/40 text-[10px] uppercase">TOTAL EVALUATED RECORDS</div>
              <div className="text-2xl font-light text-white">
                {monitoring?.prediction_count !== undefined && monitoring?.prediction_count !== null ? `${monitoring.prediction_count} Cases` : 'N/A'}
              </div>
              <div className="text-[10px] text-white/50">
                Mean Win Prob: {monitoring?.average_predicted_probability !== undefined && monitoring?.average_predicted_probability !== null
                  ? `${(monitoring.average_predicted_probability * 100).toFixed(1)}%`
                  : 'N/A'}
              </div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-2">
              <div className="text-white/40 text-[10px] uppercase">FEATURE DRIFT MONITORING</div>
              <div className="text-lg font-bold text-[#AFDDFF]">AWAITING BASELINE</div>
              <div className="text-[10px] text-white/50">Real distribution drift requires continuous feature stream tracking</div>
            </div>

            <div className="p-4 border border-white/12 bg-black space-y-2">
              <div className="text-white/40 text-[10px] uppercase">CONCEPT DRIFT MONITORING</div>
              <div className="text-lg font-bold text-white/60">INSUFFICIENT DATA</div>
              <div className="text-[10px] text-white/50">Requires post-adjudication bank disposition labels over time</div>
            </div>
          </div>

          {/* Prediction Distribution Histogram */}
          {monitoring?.prediction_distribution && (
            <div className="pt-4 border-t border-white/10 space-y-3 font-mono text-xs">
              <div className="text-white/50 text-[10px] uppercase tracking-widest">[ PREDICTION SCORE DISTRIBUTION ]</div>
              <div className="grid grid-cols-5 gap-3">
                {Object.entries(monitoring.prediction_distribution).map(([bucket, count]) => (
                  <div key={bucket} className="p-3 border border-white/10 bg-black space-y-1 text-center">
                    <div className="text-white/40 text-[10px]">{bucket}</div>
                    <div className="text-lg font-bold text-[#AFDDFF]">{count}</div>
                    <div className="text-[9px] text-white/30">cases</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <ThinDivider />

        {/* Phase 8 Feature: Human-AI Decision Feedback & Disagreement Analysis */}
        {feedback && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="HUMAN_AI_DECISION_FEEDBACK" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Human-AI Decision Alignment & Disagreement Analysis
                </h3>
              </div>
              <span className="text-[10px] font-mono text-white/40 border border-white/20 px-2 py-0.5 uppercase">[ PERSISTENT SQLITE AUDIT ]</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
              <div className="p-4 border border-white/12 bg-black space-y-1">
                <div className="text-white/40 text-[10px] uppercase">HUMAN DECISIONS LOGGED</div>
                <div className="text-2xl font-bold text-white">{feedback.total_human_decisions}</div>
                <div className="text-[10px] text-white/50">Recorded in SQLite Audit</div>
              </div>

              <div className="p-4 border border-[#9FE6C1]/40 bg-[#9FE6C1]/5 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">AGREEMENT RATE</div>
                <div className="text-2xl font-bold text-[#9FE6C1]">{(feedback.agreement_rate * 100).toFixed(1)}%</div>
                <div className="text-[10px] text-white/50">{feedback.agreement_count} Aligned Cases</div>
              </div>

              <div className="p-4 border border-[#F4C46B]/40 bg-[#F4C46B]/5 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">DISAGREEMENT RATE</div>
                <div className="text-2xl font-bold text-[#F4C46B]">{(feedback.disagreement_rate * 100).toFixed(1)}%</div>
                <div className="text-[10px] text-white/50">{feedback.disagreement_count} Overridden/Escalated</div>
              </div>

              <div className="p-4 border border-purple-400/40 bg-purple-500/5 space-y-1">
                <div className="text-white/40 text-[10px] uppercase">ESCALATION RATE</div>
                <div className="text-2xl font-bold text-purple-300">{(feedback.escalation_rate * 100).toFixed(1)}%</div>
                <div className="text-[10px] text-white/50">Senior Review Requested</div>
              </div>
            </div>

            {/* Disagreement Itemized Cases */}
            {feedback.disagreement_cases && feedback.disagreement_cases.length > 0 ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="text-white/50 text-[10px] uppercase tracking-widest">[ ITEMIZED MODEL-HUMAN DISAGREEMENTS ]</div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <thead>
                      <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                        <th className="py-3 px-4">DISPUTE_ID</th>
                        <th className="py-3 px-4">AMOUNT</th>
                        <th className="py-3 px-4">AI_REC</th>
                        <th className="py-3 px-4">WIN_PROB</th>
                        <th className="py-3 px-4">HUMAN_DECISION</th>
                        <th className="py-3 px-4">REVIEWER</th>
                        <th className="py-3 px-4">JUSTIFICATION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {feedback.disagreement_cases.map((dc) => (
                        <tr key={dc.dispute_id} className="hover:bg-white/[0.03]">
                          <td className="py-3 px-4 text-[#AFDDFF] font-bold">{dc.dispute_id}</td>
                          <td className="py-3 px-4 text-white">₹{dc.disputed_amount.toLocaleString()}</td>
                          <td className="py-3 px-4 text-white/70">{dc.ai_recommendation}</td>
                          <td className="py-3 px-4 text-white/70">{(dc.ai_win_probability * 100).toFixed(1)}%</td>
                          <td className="py-3 px-4 font-bold text-[#F4C46B]">{dc.human_decision}</td>
                          <td className="py-3 px-4 text-white/50">{dc.reviewer_id}</td>
                          <td className="py-3 px-4 text-white/70 font-sans max-w-xs truncate">"{dc.justification}"</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="p-4 border border-white/10 bg-black text-[11px] font-mono text-white/50">
                NO MODEL-HUMAN DISAGREEMENTS LOGGED YET. ALL DECISIONS ALIGN WITH AI RECOMMENDATIONS.
              </div>
            )}
          </div>
        )}

        <ThinDivider />

        {/* Phase 12 Section 4: Model Version Registry */}
        {registry && (
          <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
              <div>
                <SectionLabel label="04 // MODEL_VERSION_REGISTRY" badge="PHASE 12" />
                <h3 className="text-xl font-display font-semibold text-white mt-1">
                  Model Version Lifecycle & Deployment Registry
                </h3>
              </div>
              <TechnicalStatus
                status={`ACTIVE: ${registry.active_production_model.version_id}`}
                variant="green"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              {registry.versions.map((v) => (
                <div
                  key={v.version_id}
                  className={`p-4 border bg-black space-y-2 ${
                    v.lifecycle_status === 'PRODUCTION'
                      ? 'border-[#9FE6C1]/40 bg-[#9FE6C1]/5'
                      : 'border-white/12'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{v.version_id}</span>
                    <span className={`px-2 py-0.5 border text-[9px] font-bold uppercase ${
                      v.lifecycle_status === 'PRODUCTION'
                        ? 'border-[#9FE6C1] text-[#9FE6C1]'
                        : 'border-white/20 text-white/50'
                    }`}>
                      {v.lifecycle_status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px] text-white/60">
                    <div>Algorithm: <span className="text-white">{v.algorithm}</span></div>
                    <div>Threshold: <span className="text-[#AFDDFF] font-bold">{v.threshold}</span></div>
                    <div>Evaluated F1: <span className="text-white">{v.evaluation_f1 ?? 'N/A'}</span></div>
                    <div>Served Preds: <span className="text-white">{v.total_predictions_served}</span></div>
                  </div>

                  {v.notes && (
                    <div className="text-[10px] text-white/40 pt-1 border-t border-white/10">
                      Notes: {v.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <ThinDivider />

        {/* Phase 12 Section 5: Ground-Truth Outcome Feedback History Log */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div>
              <SectionLabel label="05 // GROUND_TRUTH_OUTCOME_FEEDBACK_LOG" badge="PHASE 12" />
              <h3 className="text-xl font-display font-semibold text-white mt-1">
                Recorded Dispute Outcomes & Ground-Truth Label Audit
              </h3>
            </div>
            <span className="text-[10px] font-mono text-white/40 border border-white/20 px-2 py-0.5 uppercase">
              {outcomes.length} PRODUCTION LABELS RECORDED
            </span>
          </div>

          {outcomes.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                    <th className="py-3 px-4">OUTCOME_ID</th>
                    <th className="py-3 px-4">DISPUTE_ID</th>
                    <th className="py-3 px-4">ACTUAL_OUTCOME</th>
                    <th className="py-3 px-4">RECOVERY_AMOUNT</th>
                    <th className="py-3 px-4">FINANCIAL_STATUS</th>
                    <th className="py-3 px-4">REVIEWER</th>
                    <th className="py-3 px-4">JUSTIFICATION</th>
                    <th className="py-3 px-4">RECORDED_AT</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {outcomes.map((o) => (
                    <tr key={o.outcome_id} className="hover:bg-white/[0.03]">
                      <td className="py-3 px-4 text-white/40 font-mono text-[10px]">{o.outcome_id}</td>
                      <td className="py-3 px-4 text-[#AFDDFF] font-bold">{o.dispute_id}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 border text-[10px] font-bold ${
                          o.actual_outcome === 'WON' ? 'border-[#9FE6C1] text-[#9FE6C1] bg-[#9FE6C1]/10' :
                          o.actual_outcome === 'LOST' ? 'border-[#E68A8A] text-[#E68A8A] bg-[#E68A8A]/10' :
                          'border-[#F4C46B] text-[#F4C46B] bg-[#F4C46B]/10'
                        }`}>
                          {o.actual_outcome}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-white font-bold">
                        {o.financial_recovery_amount !== null && o.financial_recovery_amount !== undefined
                          ? `₹${o.financial_recovery_amount.toLocaleString('en-IN')}`
                          : '—'}
                      </td>
                      <td className="py-3 px-4 text-white/60 text-[10px]">{o.financial_status}</td>
                      <td className="py-3 px-4 text-white/50">{o.reviewer_id}</td>
                      <td className="py-3 px-4 text-white/70 font-sans max-w-xs truncate">"{o.justification}"</td>
                      <td className="py-3 px-4 text-white/40 text-[10px]">
                        {new Date(o.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 border border-white/10 bg-black text-[11px] font-mono text-white/50">
              NO GROUND-TRUTH PRODUCTION OUTCOMES RECORDED YET. RECORD OUTCOMES FROM CASE DETAILS PAGE TO FEED THE CONTINUOUS LEARNING ENGINE.
            </div>
          )}
        </div>

        <ThinDivider />

        {/* Known Limitations Notice */}
        <div className="border border-[#F4C46B]/40 bg-[#F4C46B]/5 p-6 font-mono text-xs text-[#F4C46B] space-y-2 leading-relaxed">
          <div className="font-bold uppercase tracking-wider">[ MODEL SCOPE & GOVERNANCE BOUNDARIES ]</div>
          <p className="opacity-90">
            This continuous learning decision engine optimizes cost-sensitive risk reduction based on empirical ground-truth feedback.
            Autonomous retraining is disabled; model threshold transitions require explicit Admin authorization.
          </p>
        </div>
      </div>

      {/* Admin Threshold Modal */}
      {thresholds && (
        <ThresholdApprovalModal
          currentThreshold={thresholds.current_threshold}
          recommendedThreshold={thresholds.recommended_threshold || 0.35}
          isOpen={showThresholdModal}
          onClose={() => setShowThresholdModal(false)}
          onSuccess={() => {
            fetchModelData();
          }}
        />
      )}
    </div>
  );
};
