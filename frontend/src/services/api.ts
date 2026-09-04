import {
  CaseListResponse,
  CaseDetail,
  PredictionResponse,
  ExplanationResponse,
  VerifiedInvestigationResponse,
  ReviewQueueResponse,
  ReviewCasePackage,
  DecisionType,
  DecisionRecord,
  AuditLogResponse,
  ModelPerformanceResponse,
  AnalyticsOverviewResponse,
  DecisionAnalytics,
  RiskAnalytics,
  FinancialAnalytics,
  EvidenceAnalytics,
  SubsystemStatus,
  OperationalReportResponse,
  OperationsOverview,
  OperationalAlert,
  ModelMonitoringInfo,
  ModelFeedbackInfo,
  CaseTimeline,
  SimulationEvent,
  SimulationStatus,
  SimulationScenarioDetail,
  GeneratedSimTransaction,
  CaseNote,
  CaseActivityItem,
  SLAInfo,
  EvidenceConfidenceInfo,
  OutcomeOverview,
  EvidenceDocument
} from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function getAuthHeaders(extraHeaders?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders
  };
  const token = localStorage.getItem('chargeshield_auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function authFetch(url: string, init?: RequestInit): Promise<Response> {
  const headers = getAuthHeaders(init?.headers as Record<string, string>);
  return fetch(url, { ...init, headers });
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('chargeshield_auth_token');
      localStorage.removeItem('chargeshield_auth_user');
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login?session_expired=true';
      }
    }
    let errorDetail = `HTTP error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData.error) {
        errorDetail = errorData.error;
      }
    } catch {
      // Ignore JSON parse errors
    }
    const err = new Error(errorDetail) as any;
    err.status = response.status;
    throw err;
  }
  return response.json();
}

const apiCache = new Map<string, { timestamp: number; data: any }>();
const CACHE_TTL_MS = 10000; // 10s TTL for GET requests

export function clearApiCache() {
  apiCache.clear();
}

async function authFetchCached<T>(url: string, init?: RequestInit, ttlMs = CACHE_TTL_MS): Promise<T> {
  const method = (init?.method || 'GET').toUpperCase();
  const token = localStorage.getItem('chargeshield_auth_token') || 'anon';
  const cacheKey = `${token}::${url}`;

  if (method === 'GET') {
    const cached = apiCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < ttlMs) {
      return cached.data as T;
    }
  }
  const res = await authFetch(url, init);
  const data = await handleResponse<T>(res);
  if (method === 'GET') {
    apiCache.set(cacheKey, { timestamp: Date.now(), data });
  }
  return data;
}

export const api = {
  clearCache: clearApiCache,

  getHealth: async () => {
    return authFetchCached<{ status: string; environment: string }>(`${API_BASE_URL}/health`, undefined, 5000);
  },

  getCases: async (page = 1, pageSize = 20, search?: string) => {
    const query = new URLSearchParams();
    query.append('page', page.toString());
    query.append('page_size', pageSize.toString());
    if (search && search.trim()) query.append('search', search.trim());
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases?${query.toString()}`);
    return handleResponse<CaseListResponse>(res);
  },

  getCaseDetail: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}`);
    return handleResponse<CaseDetail>(res);
  },

  getPrediction: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/prediction`);
    return handleResponse<PredictionResponse>(res);
  },

  getExplanation: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/explanation`);
    return handleResponse<ExplanationResponse>(res);
  },

  getDecisionSimulation: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/simulate`);
    return handleResponse<any>(res);
  },

  getInvestigation: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/investigate`, {
      method: 'POST'
    });
    return handleResponse<VerifiedInvestigationResponse>(res);
  },

  getReviewQueue: async (filters?: {
    status?: string;
    recommendation?: string;
    minProb?: number;
    maxProb?: number;
    page?: number;
    pageSize?: number;
  }) => {
    const query = new URLSearchParams();
    if (filters?.status && filters.status !== 'ALL') query.append('status', filters.status);
    if (filters?.recommendation && filters.recommendation !== 'ALL') query.append('recommendation', filters.recommendation);
    if (filters?.minProb !== undefined) query.append('min_prob', filters.minProb.toString());
    if (filters?.maxProb !== undefined) query.append('max_prob', filters.maxProb.toString());
    if (filters?.page !== undefined) query.append('page', filters.page.toString());
    if (filters?.pageSize !== undefined) query.append('page_size', filters.pageSize.toString());

    const queryString = query.toString() ? `?${query.toString()}` : '';
    const res = await authFetch(`${API_BASE_URL}/api/v1/review/queue${queryString}`);
    return handleResponse<ReviewQueueResponse>(res);
  },

  getAuditLog: async (filters?: {
    disputeId?: string;
    reviewerId?: string;
    decision?: string;
    page?: number;
    pageSize?: number;
  }) => {
    const query = new URLSearchParams();
    if (filters?.disputeId && filters.disputeId.trim()) query.append('dispute_id', filters.disputeId.trim());
    if (filters?.reviewerId && filters.reviewerId.trim()) query.append('reviewer_id', filters.reviewerId.trim());
    if (filters?.decision && filters.decision !== 'ALL') query.append('decision', filters.decision);
    if (filters?.page !== undefined) query.append('page', filters.page.toString());
    if (filters?.pageSize !== undefined) query.append('page_size', filters.pageSize.toString());

    const queryString = query.toString() ? `?${query.toString()}` : '';
    const res = await authFetch(`${API_BASE_URL}/api/v1/review/audit${queryString}`);
    return handleResponse<AuditLogResponse>(res);
  },

  getReviewCasePackage: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/review/cases/${disputeId}`);
    return handleResponse<ReviewCasePackage>(res);
  },

  submitDecision: async (disputeId: string, reviewerId: string, decision: DecisionType, reason: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/review/cases/${disputeId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_id: reviewerId, decision, reason })
    });
    return handleResponse<DecisionRecord>(res);
  },

  getModelPerformance: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/performance`);
    return handleResponse<ModelPerformanceResponse>(res);
  },

  // Phase 9 Analytics API Methods

  getAnalyticsOverview: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/overview`);
    return handleResponse<AnalyticsOverviewResponse>(res);
  },

  getDecisionAnalytics: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/decisions`);
    return handleResponse<DecisionAnalytics>(res);
  },

  getRiskAnalytics: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/risk-distribution`);
    return handleResponse<RiskAnalytics>(res);
  },

  getFinancialAnalytics: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/financial`);
    return handleResponse<FinancialAnalytics>(res);
  },

  getEvidenceAnalytics: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/evidence`);
    return handleResponse<EvidenceAnalytics>(res);
  },

  getAnalyticsHealth: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/health`);
    return handleResponse<SubsystemStatus>(res);
  },

  getOperationalReport: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/report`);
    return handleResponse<OperationalReportResponse>(res);
  },

  getDataQuality: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/quality`);
    return handleResponse<any>(res);
  },

  getAlerts: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/analytics/alerts`);
    return handleResponse<any[]>(res);
  },

  // Phase 8 Real-Time Fraud Operations & Monitoring API Methods

  getOperationsOverview: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/operations/overview`);
    return handleResponse<OperationsOverview>(res);
  },

  getOperationsAlerts: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/operations/alerts`);
    return handleResponse<OperationalAlert[]>(res);
  },

  getOperationsHealth: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/operations/health`);
    return handleResponse<SubsystemStatus>(res);
  },

  getModelMonitoring: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/monitoring`);
    return handleResponse<ModelMonitoringInfo>(res);
  },

  getModelFeedback: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/feedback`);
    return handleResponse<ModelFeedbackInfo>(res);
  },

  getCaseTimeline: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/timeline`);
    return handleResponse<CaseTimeline>(res);
  },

  // Phase 9 Real-Time Event Intelligence & Simulation API Methods

  startSimulation: async (scenario = 'NORMAL_TRANSACTION') => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario })
    });
    return handleResponse<SimulationStatus>(res);
  },

  stopSimulation: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/simulation/stop`, {
      method: 'POST'
    });
    return handleResponse<SimulationStatus>(res);
  },

  getSimulationStatus: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/simulation/status`);
    return handleResponse<SimulationStatus>(res);
  },

  generateSimulationTransaction: async (scenario?: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/simulation/transaction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario })
    });
    return handleResponse<GeneratedSimTransaction>(res);
  },

  getSimulationEvents: async (limit = 50, dataState?: string, disputeId?: string) => {
    const query = new URLSearchParams();
    query.append('limit', limit.toString());
    if (dataState) query.append('data_state', dataState);
    if (disputeId) query.append('dispute_id', disputeId);
    const res = await authFetch(`${API_BASE_URL}/api/v1/simulation/events?${query.toString()}`);
    return handleResponse<SimulationEvent[]>(res);
  },

  getSimulationScenarios: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/simulation/scenarios`);
    return handleResponse<SimulationScenarioDetail[]>(res);
  },

  // Phase 10 API Methods
  assignCase: async (disputeId: string, reviewerId: string, actorId?: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/assignment`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_id: reviewerId, actor_id: actorId })
    });
    return handleResponse<any>(res);
  },

  updateCaseStatus: async (disputeId: string, status: string, actorId?: string, reason?: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, actor_id: actorId, reason })
    });
    return handleResponse<any>(res);
  },

  addCaseNote: async (disputeId: string, authorId: string, noteText: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ author_id: authorId, note_text: noteText })
    });
    return handleResponse<any>(res);
  },

  getCaseNotes: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/notes`);
    return handleResponse<CaseNote[]>(res);
  },

  getCaseActivity: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/activity`);
    return handleResponse<CaseActivityItem[]>(res);
  },

  getCaseSLA: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/sla`);
    return handleResponse<SLAInfo>(res);
  },

  getEvidenceConfidence: async (disputeId: string) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${disputeId}/evidence-confidence`);
    return handleResponse<EvidenceConfidenceInfo>(res);
  },

  getOutcomeOverview: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/outcomes/overview`);
    return handleResponse<OutcomeOverview>(res);
  },

  getOutcomeFeedback: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/outcomes/feedback`);
    return handleResponse<any>(res);
  },

  recordOutcome: async (payload: {
    dispute_id: string;
    actual_outcome: 'WON' | 'LOST' | 'EXPIRED';
    resolution_timestamp?: string;
    financial_recovery_amount?: number | null;
    justification: string;
  }) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/outcomes`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    return handleResponse<any>(res);
  },

  getDisputeOutcomes: async (disputeId?: string) => {
    const query = disputeId ? `?dispute_id=${encodeURIComponent(disputeId)}` : '';
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/outcomes${query}`);
    return handleResponse<any>(res);
  },

  getModelCalibration: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/calibration`);
    return handleResponse<any>(res);
  },

  getModelThresholds: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/thresholds`);
    return handleResponse<any>(res);
  },

  approveModelThreshold: async (payload: {
    proposed_threshold: number;
    reason: string;
    evidence_metrics?: Record<string, any>;
  }) => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/thresholds/approve`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    return handleResponse<any>(res);
  },

  getModelRegistry: async () => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/registry`);
    return handleResponse<any>(res);
  },

  getContinuousLearning: async (timeframe: string = '30D') => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/model/learning?timeframe=${timeframe}`);
    return handleResponse<any>(res);
  },

  // Evidence Management API methods
  uploadEvidence: async (disputeId: string, file: File): Promise<EvidenceDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    const headers: Record<string, string> = {};
    const token = localStorage.getItem('chargeshield_auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE_URL}/api/v1/cases/${encodeURIComponent(disputeId)}/evidence-upload`, {
      method: 'POST',
      headers,
      body: formData
    });
    return handleResponse<EvidenceDocument>(res);
  },

  getEvidenceList: async (disputeId: string): Promise<EvidenceDocument[]> => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${encodeURIComponent(disputeId)}/evidence`);
    const data = await handleResponse<{ dispute_id: string; evidence_documents: EvidenceDocument[] }>(res);
    return data.evidence_documents || [];
  },

  downloadEvidenceBlob: async (disputeId: string, evidenceId: string): Promise<{ blob: Blob; filename: string }> => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${encodeURIComponent(disputeId)}/evidence/${encodeURIComponent(evidenceId)}`);
    if (!res.ok) {
      throw new Error(`Failed to download evidence document ${evidenceId}`);
    }
    const blob = await res.blob();
    const contentDisposition = res.headers.get('Content-Disposition') || '';
    let filename = `evidence_${evidenceId}`;
    const match = contentDisposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
    return { blob, filename };
  },

  revokeEvidence: async (disputeId: string, evidenceId: string): Promise<EvidenceDocument> => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${encodeURIComponent(disputeId)}/evidence/${encodeURIComponent(evidenceId)}`, {
      method: 'DELETE'
    });
    return handleResponse<EvidenceDocument>(res);
  },

  exportRepresentmentPackage: async (disputeId: string): Promise<{ blob: Blob; filename: string }> => {
    const res = await authFetch(`${API_BASE_URL}/api/v1/cases/${encodeURIComponent(disputeId)}/representment-package`);
    if (!res.ok) {
      await handleResponse<never>(res);
    }
    const blob = await res.blob();
    const contentDisposition = res.headers.get('Content-Disposition') || '';
    let filename = `chargeshield_representment_${disputeId}.pdf`;
    const match = contentDisposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
    return { blob, filename };
  }
};
