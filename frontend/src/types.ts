export interface DisputeSummary {
  dispute_id: string;
  disputed_amount: number;
  currency: string;
  dispute_reason_code: string;
  dispute_status: string;
  response_deadline: string;
}

export interface CustomerSummary {
  customer_id: string;
  tenure_days: number;
  historical_chargeback_count: number;
  successful_order_count: number;
  customer_segment: string;
}

export interface OrderSummary {
  order_id: string;
  order_amount: number;
  order_timestamp: string;
  product_category: string;
  fulfillment_status: string;
}

export interface TransactionSummary {
  transaction_id: string;
  payment_method: string;
  auth_risk_score: number;
  cvv_match: string;
  avs_match: string;
  ip_country: string;
}

export interface DeliverySummary {
  delivery_id: string;
  carrier: string;
  delivery_status: string;
  pod_signature_present: boolean;
  pod_match_status: string;
  delivery_timestamp: string;
}

export interface CaseSummaryItem {
  dispute: DisputeSummary;
  customer: CustomerSummary;
  order: OrderSummary;
  transaction: TransactionSummary;
  delivery: DeliverySummary;
}

export interface CaseListResponse {
  cases: CaseSummaryItem[];
  total: number;
  is_synthetic_data: boolean;
  disclaimer: string;
}

export interface FinancialImpact {
  disputed_amount: number;
  currency: string;
  expected_recovery: number;
  expected_loss: number;
  potential_recovery_value: number;
  estimated_operational_cost: number;
  expected_net_contest_value: number;
  expected_net_accept_value: number;
  net_financial_advantage: number;
  is_financially_viable: boolean;
  assumptions: {
    base_filing_fee: number;
    contest_fee_multiplier: number;
    currency: string;
    disclaimer: string;
  };
}

export interface RiskClassification {
  dispute_id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  dispute_reason: string;
  risk_score: number;
  win_probability: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priority_score: number;
  priority_reasoning: string;
  recommended_action: string;
  confidence: number;
  model_version: string;
  prediction_timestamp: string;
}

export interface ScenarioDetail {
  action: string;
  label: string;
  expected_recovery: number;
  operational_cost: number;
  net_financial_outcome: number;
  risk_impact: string;
  type: 'MODEL_ESTIMATE' | 'ACTUAL_OUTCOME';
}

export interface DecisionSimulation {
  dispute_id: string;
  disputed_amount: number;
  win_probability: number;
  scenarios: {
    CONTEST: ScenarioDetail;
    DO_NOT_CONTEST: ScenarioDetail;
    ESCALATE: ScenarioDetail;
  };
  recommended_scenario: string;
  net_financial_advantage: number;
  actual_outcome?: {
    decision_id: string;
    reviewer_id: string;
    decision: string;
    reason: string;
    recorded_at: string;
    type: 'ACTUAL_OUTCOME';
  };
  assumptions: any;
  disclaimer: string;
}

export interface DataQualityIssue {
  rule: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  affected_records: number;
}

export interface DataQualityInfo {
  data_quality_score: number;
  status: 'EXCELLENT' | 'GOOD' | 'DEGRADED' | 'DATASET_UNAVAILABLE';
  issues: DataQualityIssue[];
  total_records_checked: number;
  passed_checks: number;
  total_checks: number;
}

export interface CaseDetail {
  dispute: DisputeSummary;
  customer: CustomerSummary;
  order: OrderSummary;
  transaction: TransactionSummary;
  delivery: DeliverySummary;
  priority?: string;
  priority_reasoning?: string;
  financial_impact?: FinancialImpact;
  risk_classification?: RiskClassification;
  executive_explanation?: string;
  technical_shap?: any;
  decision_simulation?: DecisionSimulation;
  data_quality_info?: DataQualityInfo;
}

export interface PredictionResponse {
  dispute_id: string;
  win_probability: number;
  decision_threshold: number;
  recommendation: 'CONTEST' | 'DO_NOT_CONTEST';
  model_version: string;
  is_synthetic_data: boolean;
  disclaimer: string;
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface ExplanationResponse {
  dispute_id: string;
  win_probability: number;
  recommendation: 'CONTEST' | 'DO_NOT_CONTEST';
  shap_base_value: number;
  top_positive_features: FeatureImportanceItem[];
  top_negative_features: FeatureImportanceItem[];
  model_version: string;
  is_synthetic_data: boolean;
  disclaimer: string;
}

export interface TimelineStep {
  step: number;
  action: string;
  result: string;
}

export interface FactorDetail {
  title: string;
  explanation: string;
  source_id?: string;
}

export interface EvidenceSource {
  source_id: string;
  source_type: string;
  description: string;
}

export interface InvestigationReport {
  dispute_id: string;
  disputed_amount: number;
  dispute_reason: string;
  customer_id: string;
  order_id: string;
  transaction_id: string;
  delivery_id: string;
  executive_summary: string;
  timeline: TimelineStep[];
  supporting_factors: FactorDetail[];
  risk_factors: FactorDetail[];
  evidence_sources: EvidenceSource[];
  ml_win_probability: number;
  ml_recommendation: string;
  model_version: string;
  decision_threshold: number;
  open_questions: string[];
  human_review_items: string[];
  is_synthetic_data: boolean;
  disclaimer: string;
}

export interface EvidenceVerificationResult {
  evidence_id: string;
  claim: string;
  claimed_value: string;
  actual_source_value: string;
  verification_status: 'VERIFIED' | 'MISMATCH' | 'UNVERIFIABLE';
  citation_label: string;
  source_field?: string;
}

export interface VerificationSummary {
  total_evidence: number;
  verified: number;
  mismatched: number;
  unverifiable: number;
  verification_rate: number;
}

export interface VerifiedInvestigationResponse {
  dispute_id: string;
  verification_summary: VerificationSummary;
  verification_results: EvidenceVerificationResult[];
  investigation: InvestigationReport;
  is_synthetic_data: boolean;
  disclaimer: string;
}

export type ReviewState = 'PENDING_REVIEW' | 'IN_REVIEW' | 'DECIDED' | 'ESCALATE' | 'ESCALATED';
export type DecisionType = 'CONTEST' | 'DO_NOT_CONTEST' | 'ESCALATE';

export interface ReviewQueueItem {
  dispute_id: string;
  disputed_amount: number;
  currency: string;
  dispute_reason: string;
  win_probability: number;
  ai_recommendation: string;
  verification_rate: number;
  review_status: ReviewState;
  priority_score: number;
  created_at: string;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
  pending_count: number;
  decided_count: number;
  escalated_count: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}

export interface DecisionRecord {
  decision_id: string;
  dispute_id: string;
  reviewer_id: string;
  decision: DecisionType;
  reason: string;
  ai_recommendation: string;
  ai_win_probability: number;
  verification_rate: number;
  created_at: string;
}

export interface AuditLogResponse {
  items: DecisionRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  is_synthetic_data?: boolean;
  disclaimer?: string;
}

export interface ReviewCasePackage {
  dispute_id: string;
  case: CaseDetail;
  prediction: PredictionResponse;
  investigation: InvestigationReport;
  verification: VerifiedInvestigationResponse;
  review_status: ReviewState;
  decisions: DecisionRecord[];
  is_synthetic_data: boolean;
  disclaimer: string;
}

export interface ModelPerformanceResponse {
  model_metadata: {
    model_name: string;
    model_version: string;
    primary_algorithm: string;
    baseline_algorithm: string;
    random_seed: number;
    optimal_cost_threshold: number;
    validation_min_cost_inr: number;
    train_samples: number;
    val_samples: number;
    test_samples: number;
  };
  evaluation_report: {
    dataset_summary: {
      test_disputes: number;
      test_won_count: number;
      test_lost_count: number;
      test_win_rate_percent: number;
    };
    baseline_logistic_regression: {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      roc_auc: number;
      pr_auc: number;
      brier_score: number;
    };
    "primary_lightgbm_default_0.50": {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      roc_auc: number;
      pr_auc: number;
      brier_score: number;
    };
    primary_lightgbm_optimal_threshold: {
      threshold: number;
      metrics: {
        accuracy: number;
        precision: number;
        recall: number;
        f1_score: number;
        roc_auc: number;
        pr_auc: number;
        brier_score: number;
      };
    };
    financial_cost_simulation_inr: {
      cost_naive_always_contest: number;
      "cost_model_default_0.50": number;
      cost_model_optimal_threshold: number;
      cost_savings_inr: number;
    };
  };
  is_synthetic_data: boolean;
  disclaimer: string;
}

// Phase 9 Analytics Interfaces

export interface OperationalMetrics {
  total_cases: number;
  pending_review: number;
  in_review: number;
  decided: number;
  escalated: number;
  contest_decisions: number;
  do_not_contest_decisions: number;
  escalations: number;
  avg_review_activity: string;
}

export interface FinancialAnalytics {
  total_disputed_value: number;
  contest_value: number;
  do_not_contest_value: number;
  escalate_value: number;
  simulated_recoverable_value: number;
  currency: string;
  disclaimer: string;
}

export interface DecisionAnalytics {
  ai_recommendation_distribution: Record<string, number>;
  human_decision_distribution: Record<string, number>;
  agreement_rate: number;
  disagreement_count: number;
  total_human_decisions: number;
  escalation_rate: number;
}

export interface RiskAnalytics {
  win_probability_buckets: Record<string, number>;
  dispute_reason_distribution: Record<string, number>;
  disputed_amount_distribution: Record<string, number>;
  high_priority_count: number;
}

export interface EvidenceAnalytics {
  total_cases_analyzed: number;
  verified_evidence_count: number;
  mismatched_evidence_count: number;
  unverifiable_evidence_count: number;
  overall_verification_rate: number;
  has_historical_persistence: boolean;
  note: string;
}

export interface SubsystemStatus {
  api: string;
  database: string;
  ml_engine: string;
  evidence_engine: string;
  review_engine: string;
  dataset: string;
  timestamp: string;
}

export interface AnalyticsOverviewResponse {
  operational: OperationalMetrics;
  financial: FinancialAnalytics;
  decisions: DecisionAnalytics;
  risk: RiskAnalytics;
  evidence: EvidenceAnalytics;
  health: SubsystemStatus;
  generated_at: string;
}

export interface OperationalReportResponse {
  report_id: string;
  generated_at: string;
  disclaimer: string;
  model_version: string;
  operational_metrics: OperationalMetrics;
  financial_analytics: FinancialAnalytics;
  decision_analytics: DecisionAnalytics;
  risk_analytics: RiskAnalytics;
  evidence_analytics: EvidenceAnalytics;
  subsystem_health: SubsystemStatus;
}

export interface MetricValue {
  status: string;
  value?: any;
  unit?: string;
  note?: string;
}

export interface OperationsOverview {
  total_active_disputes: number;
  pending_human_reviews: number;
  high_risk_cases: number;
  critical_risk_cases: number;
  total_disputed_value: number;
  estimated_recoverable_value: number;
  decisions_today: number;
  contest_rate: number;
  do_not_contest_rate: number;
  escalation_rate: number;
  average_review_time: MetricValue;
  evidence_verification_status: string;
  data_quality_status: string;
  model_status: string;
  audit_system_status: string;
  currency: string;
  last_updated: string;
}

export interface OperationalAlert {
  alert_id: string;
  severity: 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL';
  category: string;
  title: string;
  description: string;
  detected_at: string;
  related_metric?: string;
  recommended_action: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
}

export interface ModelMonitoringInfo {
  current_model: string;
  model_version: string;
  prediction_count: number;
  average_predicted_probability: number;
  prediction_distribution: Record<string, number>;
  positive_prediction_rate: number;
  threshold_in_use: number;
  baseline_availability: boolean;
  drift_status: 'HEALTHY' | 'WARNING' | 'DRIFT_DETECTED' | 'AWAITING_BASELINE' | 'INSUFFICIENT_DATA';
  performance_status: string;
  data_state_label: string;
  last_evaluated: string;
}

export interface DisagreementCase {
  dispute_id: string;
  disputed_amount: number;
  ai_recommendation: string;
  ai_win_probability: number;
  human_decision: string;
  reviewer_id: string;
  justification: string;
  created_at: string;
}

export interface ModelFeedbackInfo {
  total_human_decisions: number;
  agreement_count: number;
  disagreement_count: number;
  agreement_rate: number;
  disagreement_rate: number;
  override_rate: number;
  escalation_rate: number;
  disagreement_cases: DisagreementCase[];
  data_state_label: string;
}

export interface TimelineEvent {
  event_id: string;
  stage: string;
  title: string;
  description: string;
  timestamp?: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING';
  actor: string;
  metadata?: Record<string, any>;
}

export interface CaseTimeline {
  dispute_id: string;
  events: TimelineEvent[];
  current_stage: string;
  overall_status: string;
}

export interface SimulationEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  dispute_id?: string;
  transaction_id?: string;
  source: string;
  data_state: 'SIMULATION' | 'HISTORICAL' | 'PRODUCTION';
  status: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface SimulationStatus {
  running: boolean;
  scenario: string;
  events_processed: number;
  transactions_processed: number;
  cases_created: number;
  last_event_time?: string;
  data_state: 'SIMULATION' | 'HISTORICAL' | 'PRODUCTION';
}

export interface SimulationScenarioDetail {
  scenario_id: string;
  name: string;
  description: string;
  target_risk_tier: string;
  target_recommendation: string;
}

export interface GeneratedSimTransaction {
  dispute_id: string;
  transaction_id: string;
  scenario: string;
  disputed_amount: number;
  win_probability: number;
  recommendation: string;
  priority: string;
  data_state: string;
}

export interface ReviewQueueItem {
  dispute_id: string;
  disputed_amount: number;
  currency: string;
  dispute_reason: string;
  win_probability: number;
  ai_recommendation: string;
  verification_rate: number;
  review_status: ReviewState;
  priority_score: number;
  created_at: string;
  assigned_reviewer_id?: string;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
  pending_count: number;
  decided_count: number;
  escalated_count: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}

export interface DecisionRecord {
  decision_id: string;
  dispute_id: string;
  reviewer_id: string;
  decision: DecisionType;
  reason: string;
  ai_recommendation: string;
  ai_win_probability: number;
  verification_rate: number;
  created_at: string;
}

export interface AuditLogResponse {
  items: DecisionRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  is_synthetic_data?: boolean;
  disclaimer?: string;
}

// Phase 10 Types: Case Operations, SLA, Evidence Confidence & Outcome Intelligence
export type CaseWorkflowStatus = 'NEW' | 'IN_REVIEW' | 'ESCALATED' | 'DECISION_PENDING' | 'RESOLVED' | 'CLOSED';

export interface CaseActivityItem {
  activity_id: string;
  dispute_id: string;
  action_type: string;
  description: string;
  performed_by: string;
  timestamp: string;
  event_type?: string;
  actor?: string;
  action?: string;
  previous_state?: string;
  new_state?: string;
  reason?: string;
}

export interface CaseNote {
  note_id: string;
  dispute_id: string;
  author_id: string;
  content: string;
  note_text?: string;
  created_at: string;
  timestamp?: string;
}

export interface SLAInfo {
  sla_status: 'ON_TRACK' | 'DUE_SOON' | 'AT_RISK' | 'OVERDUE' | 'NO_DEADLINE';
  hours_remaining?: number;
  is_overdue: boolean;
  urgency_score: number;
  review_priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  priority_explanation: string;
  deadline?: string;
  data_state: 'PRODUCTION' | 'SIMULATION' | 'HISTORICAL';
}

export interface EvidenceConfidenceInfo {
  confidence_score: number;
  evidence_confidence_score?: number;
  readiness_tier: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  evidence_status?: string;
  verified_claims_count: number;
  unverifiable_claims_count: number;
  mismatched_claims_count: number;
  pod_signature_present: boolean;
  delivery_signature_present?: boolean;
  cvv_match: string;
  avs_match: string;
  delivery_status: string;
  missing_evidence_items: string[];
  missing_evidence?: string[];
  conflicting_evidence?: string[];
  verification_summary?: string;
  data_state: 'PRODUCTION' | 'SIMULATION' | 'HISTORICAL';
}

export interface OutcomeOverview {
  total_reviewed: number;
  contest_count: number;
  do_not_contest_count: number;
  escalate_count: number;
  contest_percentage: number;
  do_not_contest_percentage: number;
  escalate_percentage: number;
  agreement_rate: number;
  disagreement_rate: number;
  total_disputed_exposure: number;
  average_disputed_amount: number;
  estimated_recoverable_value: number;
  model_estimate_status: string;
  human_decision_status: string;
  actual_outcome_status: string;
  actual_outcome_message: string;
  data_state: 'PRODUCTION' | 'SIMULATION' | 'HISTORICAL';
}

export interface ModelOutcomeRecord {
  outcome_id: string;
  dispute_id: string;
  actual_outcome: 'WON' | 'LOST' | 'EXPIRED';
  resolution_timestamp?: string;
  financial_recovery_amount?: number | null;
  financial_status: 'EXPLICIT_RECOVERY' | 'INSUFFICIENT_DATA';
  reviewer_id: string;
  justification: string;
  data_state: 'PRODUCTION' | 'SIMULATION';
  created_at: string;
}

export interface OutcomeIngestPayload {
  dispute_id: string;
  actual_outcome: 'WON' | 'LOST' | 'EXPIRED';
  resolution_timestamp?: string;
  financial_recovery_amount?: number | null;
  justification: string;
}

export interface ProbabilityBucketInfo {
  bucket_range: string;
  bucket_min: number;
  bucket_max: number;
  predicted_count: number;
  actual_win_count: number;
  avg_predicted_prob: number;
  actual_win_rate: number;
  calibration_error: number;
}

export interface CalibrationResponse {
  calibration_status: 'CALIBRATED' | 'UNDERCONFIDENT' | 'OVERCONFIDENT' | 'INSUFFICIENT_DATA';
  overall_expected_calibration_error: number;
  total_labeled_cases: number;
  buckets: ProbabilityBucketInfo[];
  recommendation: string;
  data_provenance: string;
}

export interface ThresholdEvalMetric {
  threshold: number;
  predicted_contest_count: number;
  predicted_accept_count: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  accuracy: number;
  net_financial_recovery: number;
}

export interface ThresholdOptimizationResponse {
  current_threshold: number;
  recommended_threshold?: number | null;
  optimal_f1_threshold: number;
  optimal_financial_threshold: number;
  recommendation_status: 'MAINTAIN' | 'RECOMMEND_UPDATE' | 'AWAITING_BASELINE';
  threshold_evaluations: ThresholdEvalMetric[];
  historical_audits: any[];
  data_provenance: string;
}

export interface ModelVersionRegistryItem {
  version_id: string;
  model_name: string;
  algorithm: string;
  threshold: number;
  lifecycle_status: 'DEVELOPMENT' | 'VALIDATION' | 'STAGED' | 'PRODUCTION' | 'RETIRED';
  deployed_at: string;
  evaluation_f1?: number;
  evaluation_auc?: number;
  total_predictions_served: number;
  notes?: string;
}

export interface ModelRegistryResponse {
  active_production_model: ModelVersionRegistryItem;
  versions: ModelVersionRegistryItem[];
  governance_rules: {
    no_autonomous_retraining: boolean;
    no_autonomous_threshold_change: boolean;
    admin_approval_required: boolean;
  };
}

export interface LearningMetricsResponse {
  timeframe: string;
  human_ai_agreement_rate: number;
  agreement_status: string;
  model_historical_accuracy: number;
  outcome_coverage: {
    total_production_predictions: number;
    cases_with_ground_truth: number;
    coverage_percentage: number;
  };
  pipeline_readiness: {
    status: 'READY' | 'AWAITING_OUTCOMES';
    min_required_outcomes: number;
    current_outcomes: number;
    governance: {
      no_autonomous_training: boolean;
      simulation_exclusion: boolean;
    };
  };
  data_provenance: string;
}

export interface EvidenceDocument {
  evidence_id: string;
  dispute_id: string;
  original_filename: string;
  safe_filename: string;
  content_type: string;
  file_size: number;
  sha256_hash: string;
  uploaded_by: string;
  uploaded_at: string;
  data_state: 'PRODUCTION' | 'SIMULATION';
  status: 'ACTIVE' | 'REVOKED';
  created_at: string;
  updated_at: string;
}

