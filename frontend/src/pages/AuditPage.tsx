import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { DecisionRecord, AuditLogResponse } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { AuditTimelineVisualizer } from '../components/visual/AuditTimelineVisualizer';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { EditorialImageHero } from '../components/visual/EditorialImageHero';

export interface AuditFilterState {
  disputeId: string;
  reviewerId: string;
  decision: string;
}

const initialFilters: AuditFilterState = {
  disputeId: '',
  reviewerId: '',
  decision: 'ALL'
};

export const AuditPage: React.FC = () => {
  const [auditData, setAuditData] = useState<AuditLogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Input form state (unapplied filter state)
  const [filters, setFilters] = useState<AuditFilterState>(initialFilters);

  // Active applied filters state (used for API requests and pagination)
  const [appliedFilters, setAppliedFilters] = useState<AuditFilterState>(initialFilters);

  // Pagination state
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  const navigate = useNavigate();

  const fetchAuditLog = async (currentPage: number, activeFilters: AuditFilterState) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAuditLog({
        disputeId: activeFilters.disputeId,
        reviewerId: activeFilters.reviewerId,
        decision: activeFilters.decision,
        page: currentPage,
        pageSize: pageSize
      });
      setAuditData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load persistent decision audit log from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLog(page, appliedFilters);
  }, [page, appliedFilters]);

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setAppliedFilters({ ...filters });
    if (page !== 1) {
      setPage(1);
    } else {
      fetchAuditLog(1, filters);
    }
  };

  const handleResetFilters = () => {
    setFilters(initialFilters);
    setAppliedFilters(initialFilters);
    if (page !== 1) {
      setPage(1);
    } else {
      fetchAuditLog(1, initialFilters);
    }
  };

  const totalRecords = auditData?.total || 0;

  return (
    <div className="relative min-h-screen bg-transparent">
      <AnimatedBackground variant="audit" />

      {/* Editorial Image Hero Header */}
      <EditorialImageHero
        imageSrc="/assets/audit_institutional_archive.png"
        category="06 / AUDIT_TRAIL"
        titleLines={['AUDIT', 'TRAIL']}
        subtitle="Immutable append-only SQLite log recording human risk analyst authorizations and timestamps."
        metadata={[
          { label: 'PERSISTENT STORE', value: 'SQLITE (chargeshield.db)' },
          { label: 'TOTAL RECORDED', value: `${totalRecords} DECISIONS` },
          { label: 'RECORD TYPE', value: 'APPEND-ONLY IMMUTABLE' },
        ]}
      />

      <div className="relative z-10 px-[20px] md:px-[35px] py-12 space-y-8 max-w-[1600px] mx-auto animate-lumen-fade-up">

        {/* Live Vertical Node-Chain Audit Timeline Visualizer */}
        <AuditTimelineVisualizer records={auditData?.items || []} />

        {/* Filter & Search Bar */}
        <div className="border border-white/12 p-6 bg-white/[0.01]">
          <form onSubmit={handleApplyFilters} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end font-mono text-xs">
            {/* Dispute ID Search Input */}
            <div>
              <label className="block text-[10px] text-white/40 uppercase tracking-widest mb-1">DISPUTE ID SEARCH</label>
              <input
                type="text"
                placeholder="e.g. DSP_000001"
                value={filters.disputeId}
                onChange={(e) => setFilters(prev => ({ ...prev, disputeId: e.target.value }))}
                className="w-full bg-black border border-white/20 px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-[#AFDDFF]"
              />
            </div>

            {/* Reviewer ID Input */}
            <div>
              <label className="block text-[10px] text-white/40 uppercase tracking-widest mb-1">REVIEWER ID</label>
              <input
                type="text"
                placeholder="e.g. analyst_sarah_01"
                value={filters.reviewerId}
                onChange={(e) => setFilters(prev => ({ ...prev, reviewerId: e.target.value }))}
                className="w-full bg-black border border-white/20 px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-[#AFDDFF]"
              />
            </div>

            {/* Decision Dropdown */}
            <div>
              <label className="block text-[10px] text-white/40 uppercase tracking-widest mb-1">HUMAN DECISION</label>
              <select
                value={filters.decision}
                onChange={(e) => setFilters(prev => ({ ...prev, decision: e.target.value }))}
                className="w-full bg-black border border-white/20 px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-[#AFDDFF]"
              >
                <option value="ALL">ALL DECISIONS</option>
                <option value="CONTEST">CONTEST</option>
                <option value="DO_NOT_CONTEST">DO_NOT_CONTEST</option>
                <option value="ESCALATE">ESCALATE</option>
              </select>
            </div>

            {/* Filter Action Buttons */}
            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 py-2 border border-[#AFDDFF] bg-[#AFDDFF] hover:bg-[#AFDDFF]/80 text-black font-mono font-bold text-xs uppercase tracking-wider transition-all"
              >
                APPLY FILTER
              </button>
              <button
                type="button"
                onClick={handleResetFilters}
                className="py-2 px-4 border border-white/20 hover:border-white text-white font-mono text-xs uppercase tracking-wider transition-all"
              >
                RESET
              </button>
            </div>
          </form>
        </div>

        {/* Audit Log Table Container */}
        <div className="border border-white/12 overflow-hidden bg-white/[0.01]">
          {loading ? (
            <div className="p-12 text-center text-white/50 font-mono text-xs tracking-widest uppercase flex items-center justify-center gap-3">
              <span className="h-2 w-2 bg-[#AFDDFF] animate-ping" />
              <span>RETRIEVING PERSISTENT DECISION AUDIT LOGS...</span>
            </div>
          ) : error ? (
            <div className="p-8 text-center space-y-4 font-mono text-xs">
              <div className="text-[#E68A8A] font-bold text-sm uppercase tracking-wider">{error}</div>
              <button
                onClick={() => fetchAuditLog(page, appliedFilters)}
                className="px-4 py-2 border border-[#E68A8A] text-[#E68A8A] hover:bg-[#E68A8A] hover:text-black font-mono font-bold text-xs uppercase tracking-wider transition-all"
              >
                RETRY REQUEST
              </button>
            </div>
          ) : !auditData || auditData.items.length === 0 ? (
            <div className="p-12 text-center text-white/40 font-mono text-xs space-y-4 uppercase tracking-widest">
              <div>NO HUMAN REVIEW DECISIONS MATCHING FILTER CRITERIA.</div>
              <div className="flex justify-center gap-4 pt-2">
                <button
                  onClick={handleResetFilters}
                  className="px-4 py-2 border border-white/20 text-white font-mono text-xs uppercase tracking-wider"
                >
                  RESET FILTERS
                </button>
                <button
                  onClick={() => navigate('/queue')}
                  className="px-4 py-2 border border-[#AFDDFF] bg-[#AFDDFF] text-black font-mono font-bold text-xs uppercase tracking-wider"
                >
                  AUTHORIZE A CASE IN QUEUE &rarr;
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                      <th className="py-3.5 px-4">DECISION_ID</th>
                      <th className="py-3.5 px-4">DISPUTE_ID</th>
                      <th className="py-3.5 px-4">REVIEWER_ID</th>
                      <th className="py-3.5 px-4">HUMAN_DECISION</th>
                      <th className="py-3.5 px-4">AI_CONTEXT</th>
                      <th className="py-3.5 px-4">VERIFICATION</th>
                      <th className="py-3.5 px-4">TIMESTAMP_UTC</th>
                      <th className="py-3.5 px-4">JUSTIFICATION_REASON</th>
                      <th className="py-3.5 px-4 text-right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {auditData.items.map((record: DecisionRecord) => (
                      <tr key={record.decision_id} className="hover:bg-white/[0.03] transition-colors">
                        <td className="py-3.5 px-4 font-bold text-[#AFDDFF] font-mono">
                          {record.decision_id}
                        </td>
                        <td className="py-3.5 px-4 font-bold text-white font-mono">
                          {record.dispute_id}
                        </td>
                        <td className="py-3.5 px-4 text-white/80 font-mono">
                          {record.reviewer_id}
                        </td>
                        <td className="py-3.5 px-4">
                          <StatusBadge status={record.decision} type="recommendation" />
                        </td>
                        <td className="py-3.5 px-4 text-white/80 font-mono">
                          {record.ai_recommendation} ({(record.ai_win_probability * 100).toFixed(1)}%)
                        </td>
                        <td className="py-3.5 px-4 text-[#9FE6C1] font-bold font-mono">
                          {(record.verification_rate * 100).toFixed(0)}% VERIFIED
                        </td>
                        <td className="py-3.5 px-4 text-white/50 text-[11px] font-mono whitespace-nowrap">
                          {record.created_at ? record.created_at.replace('T', ' ').substring(0, 19) : 'N/A'}
                        </td>
                        <td className="py-3.5 px-4 text-white/80 text-[11px] max-w-xs truncate font-sans">
                          "{record.reason}"
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => navigate(`/cases/${record.dispute_id}`)}
                            className="px-3 py-1.5 border border-white/20 hover:border-[#AFDDFF] hover:text-[#AFDDFF] text-white font-mono text-[11px] uppercase tracking-wider transition-all"
                          >
                            INSPECT_CASE &rarr;
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              <div className="px-6 py-4 border-t border-white/12 flex items-center justify-between font-mono text-xs bg-black">
                <div className="text-white/40 uppercase tracking-wider text-[11px]">
                  PAGE <span className="text-white font-bold">{auditData.page}</span> OF{' '}
                  <span className="text-white font-bold">{auditData.total_pages}</span> ({auditData.total} RECORDS TOTAL)
                </div>
                <div className="flex items-center gap-3">
                  <button
                    disabled={auditData.page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-4 py-1.5 border border-white/20 hover:border-[#AFDDFF] disabled:opacity-30 text-white font-mono text-xs uppercase tracking-wider transition-all"
                  >
                    [ PREV ]
                  </button>
                  <button
                    disabled={auditData.page >= auditData.total_pages}
                    onClick={() => setPage((p) => Math.min(auditData.total_pages, p + 1))}
                    className="px-4 py-1.5 border border-white/20 hover:border-[#AFDDFF] disabled:opacity-30 text-white font-mono text-xs uppercase tracking-wider transition-all"
                  >
                    [ NEXT ]
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
