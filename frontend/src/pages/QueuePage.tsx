import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { ReviewQueueItem, ReviewQueueResponse } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityStreamVisualizer } from '../components/visual/PriorityStreamVisualizer';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';
import { EditorialImageHero } from '../components/visual/EditorialImageHero';

export const QueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [queueResponse, setQueueResponse] = useState<ReviewQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state from URL or defaults
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'ALL');
  const [recFilter, setRecFilter] = useState<string>(searchParams.get('recommendation') || 'ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>(searchParams.get('priority') || 'ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkReviewer, setBulkReviewer] = useState<string>('RVR_001');
  const [bulkStatus, setBulkStatus] = useState<string>('IN_REVIEW');
  const [bulkProcessing, setBulkProcessing] = useState<boolean>(false);
  const [bulkMessage, setBulkMessage] = useState<string | null>(null);

  // Pagination state
  const [page, setPage] = useState<number>(1);
  const pageSize = 20;

  // Sort state
  const sortByParam = searchParams.get('sort_by');
  const initialSortField: keyof ReviewQueueItem = sortByParam === 'highest_amount' ? 'disputed_amount' : 'priority_score';
  const [sortField, setSortField] = useState<keyof ReviewQueueItem>(initialSortField);
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const fetchQueue = async (currentPage: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getReviewQueue({
        status: statusFilter,
        recommendation: recFilter,
        page: currentPage,
        pageSize: pageSize
      });
      setQueueResponse(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load review queue from backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue(page);
  }, [statusFilter, recFilter, page]);

  const items = queueResponse?.items || [];

  const filteredItems = items.filter(item => {
    // Priority filter
    if (priorityFilter !== 'ALL') {
      const priorityTier = item.disputed_amount >= 30000 ? 'CRITICAL' : item.win_probability >= 0.6 ? 'HIGH' : 'MEDIUM';
      if (priorityTier !== priorityFilter) return false;
    }

    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.dispute_id.toLowerCase().includes(q) ||
      item.dispute_reason.toLowerCase().includes(q) ||
      (item.assigned_reviewer_id && item.assigned_reviewer_id.toLowerCase().includes(q))
    );
  });

  const sortedItems = [...filteredItems].sort((a, b) => {
    let valA: any = a[sortField] ?? '';
    let valB: any = b[sortField] ?? '';
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  const handleSort = (field: keyof ReviewQueueItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(sortedItems.map(i => i.dispute_id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (disputeId: string) => {
    setSelectedIds(prev =>
      prev.includes(disputeId) ? prev.filter(id => id !== disputeId) : [...prev, disputeId]
    );
  };

  const handleBulkAssign = async () => {
    if (selectedIds.length === 0) return;
    try {
      setBulkProcessing(true);
      setBulkMessage(null);
      await Promise.all(selectedIds.map(id => api.assignCase(id, bulkReviewer, 'SUPERVISOR_01')));
      setBulkMessage(`Successfully assigned ${selectedIds.length} case(s) to ${bulkReviewer}.`);
      setSelectedIds([]);
      fetchQueue(page);
    } catch (err: any) {
      setBulkMessage(`Bulk assignment error: ${err.message}`);
    } finally {
      setBulkProcessing(false);
    }
  };

  const handleBulkStatusChange = async () => {
    if (selectedIds.length === 0) return;
    try {
      setBulkProcessing(true);
      setBulkMessage(null);
      await Promise.all(selectedIds.map(id => api.updateCaseStatus(id, bulkStatus, 'SUPERVISOR_01', 'Bulk workflow update')));
      setBulkMessage(`Successfully updated ${selectedIds.length} case(s) to ${bulkStatus}.`);
      setSelectedIds([]);
      fetchQueue(page);
    } catch (err: any) {
      setBulkMessage(`Bulk status update error: ${err.message}`);
    } finally {
      setBulkProcessing(false);
    }
  };

  const totalPages = queueResponse?.total_pages || 1;
  const totalCount = queueResponse?.total || 0;

  return (
    <div className="relative min-h-screen bg-[#080B10]">
      <AnimatedBackground variant="queue" />

      <EditorialImageHero
        imageSrc="/assets/queue_transaction_stream.png"
        category="02 / REVIEW_QUEUE"
        titleLines={['REVIEW', 'QUEUE']}
        subtitle="Operational triage stream ordered by transparent LightGBM win probability & priority scoring."
        metadata={[
          { label: 'TOTAL QUEUED', value: `${totalCount} CASES` },
          { label: 'ACTIVE PAGE', value: `PAGE ${page} OF ${totalPages}` },
          { label: 'SELECTED', value: `${selectedIds.length} CASES` },
        ]}
      />

      <div className="relative z-10 px-[20px] md:px-[35px] py-12 space-y-8 max-w-[1600px] mx-auto animate-lumen-fade-up">
        {/* Header & Filter Controls Strip */}
        <div className="border border-white/12 p-6 bg-white/[0.01] space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/12 pb-4">
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-[#AFDDFF] animate-pulse" />
              <span className="text-white font-bold font-display text-sm tracking-wider uppercase">FILTER REVIEW STREAM</span>
            </div>

            {/* Search Box */}
            <div className="relative">
              <input
                type="text"
                placeholder="FILTER DISPUTE ID, REASON, OR REVIEWER..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-black border border-white/20 px-3 py-1.5 text-xs text-white placeholder-white/40 focus:outline-none focus:border-[#AFDDFF] font-mono w-80 transition-all"
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-6 font-mono text-xs">
            <div className="flex items-center gap-2">
              <span className="text-white/40 uppercase tracking-widest text-[10px]">STATUS:</span>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-black border border-white/20 px-3 py-1 text-white focus:outline-none focus:border-[#AFDDFF] text-xs font-mono"
              >
                <option value="ALL">ALL STATUSES</option>
                <option value="NEW">NEW</option>
                <option value="PENDING_REVIEW">PENDING REVIEW</option>
                <option value="IN_REVIEW">IN REVIEW</option>
                <option value="ESCALATED">ESCALATED</option>
                <option value="DECISION_PENDING">DECISION PENDING</option>
                <option value="RESOLVED">RESOLVED</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-white/40 uppercase tracking-widest text-[10px]">AI RECOMMENDATION:</span>
              <select
                value={recFilter}
                onChange={(e) => {
                  setRecFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-black border border-white/20 px-3 py-1 text-white focus:outline-none focus:border-[#AFDDFF] text-xs font-mono"
              >
                <option value="ALL">ALL RECOMMENDATIONS</option>
                <option value="CONTEST">CONTEST</option>
                <option value="DO_NOT_CONTEST">DO NOT CONTEST</option>
                <option value="ESCALATE">ESCALATE</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-white/40 uppercase tracking-widest text-[10px]">PRIORITY TIER:</span>
              <select
                value={priorityFilter}
                onChange={(e) => {
                  setPriorityFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-black border border-white/20 px-3 py-1 text-white focus:outline-none focus:border-[#AFDDFF] text-xs font-mono"
              >
                <option value="ALL">ALL PRIORITY TIERS</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
              </select>
            </div>

            <div className="ml-auto text-white/40 text-[11px]">
              SHOWING <span className="text-[#AFDDFF] font-bold">{sortedItems.length}</span> OF {totalCount} DISPUTES
            </div>
          </div>

          {/* Bulk Operations Bar */}
          {selectedIds.length > 0 && (
            <div className="pt-4 border-t border-white/12 flex flex-wrap items-center justify-between gap-4 font-mono text-xs bg-[#AFDDFF]/5 p-3 border border-[#AFDDFF]/30">
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 bg-[#AFDDFF] text-black font-bold text-[10px] uppercase">
                  {selectedIds.length} SELECTED
                </span>
                <span className="text-white/70">Bulk Operational Workflow Actions:</span>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-white/40 text-[10px]">ASSIGN TO:</span>
                  <select
                    value={bulkReviewer}
                    onChange={(e) => setBulkReviewer(e.target.value)}
                    className="bg-black border border-white/30 text-white px-2 py-1 text-xs"
                  >
                    <option value="RVR_001">REV_001 (Senior Analyst)</option>
                    <option value="RVR_002">REV_002 (Fraud Specialist)</option>
                    <option value="RVR_TEAM_ALPHA">TEAM ALPHA</option>
                  </select>
                  <button
                    onClick={handleBulkAssign}
                    disabled={bulkProcessing}
                    className="px-3 py-1 border border-[#AFDDFF] text-[#AFDDFF] hover:bg-[#AFDDFF] hover:text-black font-bold text-xs uppercase transition-all"
                  >
                    ASSIGN
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-white/40 text-[10px]">SET STATUS:</span>
                  <select
                    value={bulkStatus}
                    onChange={(e) => setBulkStatus(e.target.value)}
                    className="bg-black border border-white/30 text-white px-2 py-1 text-xs"
                  >
                    <option value="IN_REVIEW">IN REVIEW</option>
                    <option value="ESCALATED">ESCALATED</option>
                    <option value="DECISION_PENDING">DECISION PENDING</option>
                  </select>
                  <button
                    onClick={handleBulkStatusChange}
                    disabled={bulkProcessing}
                    className="px-3 py-1 border border-white/40 text-white hover:bg-white hover:text-black font-bold text-xs uppercase transition-all"
                  >
                    UPDATE WORKFLOW
                  </button>
                </div>
              </div>
            </div>
          )}

          {bulkMessage && (
            <div className="text-[11px] font-mono text-[#9FE6C1] border border-[#9FE6C1]/30 p-2 bg-[#9FE6C1]/10">
              {bulkMessage}
            </div>
          )}
        </div>

        {/* Live Animated Triage Priority Stream */}
        <PriorityStreamVisualizer items={items} />

        {/* Main Data Table Panel */}
        <div className="border border-white/12 overflow-hidden bg-white/[0.01]">
          {loading ? (
            <div className="p-12 text-center text-white/50 font-mono text-xs tracking-widest uppercase flex items-center justify-center gap-3">
              <span className="h-2 w-2 bg-[#AFDDFF] animate-ping" />
              <span>FETCHING OPERATIONAL REVIEW QUEUE...</span>
            </div>
          ) : error ? (
            <div className="p-8 text-center space-y-4 font-mono text-xs">
              <div className="text-[#E68A8A] font-bold text-sm uppercase tracking-wider">
                {error}
              </div>
              <button
                onClick={() => fetchQueue(page)}
                className="px-4 py-2 border border-[#E68A8A] text-[#E68A8A] hover:bg-[#E68A8A] hover:text-black font-mono font-bold text-xs uppercase tracking-wider transition-all"
              >
                RETRY REQUEST
              </button>
            </div>
          ) : sortedItems.length === 0 ? (
            <div className="p-12 text-center text-white/40 font-mono text-xs uppercase tracking-widest">
              NO DISPUTE CASES MATCHING CURRENT FILTERS.
            </div>
          ) : (
            <div>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-white/12 text-white/40 uppercase tracking-widest text-[10px] bg-black">
                      <th className="py-3.5 px-4 w-10 text-center">
                        <input
                          type="checkbox"
                          checked={selectedIds.length === sortedItems.length && sortedItems.length > 0}
                          onChange={(e) => handleSelectAll(e.target.checked)}
                          className="accent-[#AFDDFF] cursor-pointer"
                        />
                      </th>
                      <th className="py-3.5 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('dispute_id')}>
                        DISPUTE_ID
                      </th>
                      <th className="py-3.5 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('disputed_amount')}>
                        AMOUNT (INR)
                      </th>
                      <th className="py-3.5 px-4">REASON_CODE</th>
                      <th className="py-3.5 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('win_probability')}>
                        WIN_PROBABILITY
                      </th>
                      <th className="py-3.5 px-4">AI_RECOMMENDATION</th>
                      <th className="py-3.5 px-4">NET_RECOVERY_ESTIMATE</th>
                      <th className="py-3.5 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('priority_score')}>
                        PRIORITY_TIER
                      </th>
                      <th className="py-3.5 px-4">WORKFLOW_STATUS</th>
                      <th className="py-3.5 px-4 text-right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {sortedItems.map((item) => {
                      const netAdvantage = Math.round(item.disputed_amount * item.win_probability - 1875);
                      const priorityTier = item.disputed_amount >= 30000 ? 'CRITICAL' : item.win_probability >= 0.6 ? 'HIGH' : 'MEDIUM';
                      const isSelected = selectedIds.includes(item.dispute_id);
                      return (
                        <tr
                          key={item.dispute_id}
                          className={`hover:bg-white/[0.03] transition-colors ${isSelected ? 'bg-[#AFDDFF]/5' : ''}`}
                        >
                          <td className="py-3.5 px-4 text-center">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleSelect(item.dispute_id)}
                              className="accent-[#AFDDFF] cursor-pointer"
                            />
                          </td>
                          <td className="py-3.5 px-4 font-bold text-white">
                            <div>{item.dispute_id}</div>
                            {item.assigned_reviewer_id && (
                              <div className="text-[9px] text-white/40 uppercase">RVR: {item.assigned_reviewer_id}</div>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-white/80">
                            ₹{item.disputed_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3.5 px-4 text-white/50 text-[11px] max-w-[180px] truncate">
                            {item.dispute_reason}
                          </td>
                          <td className="py-3.5 px-4 font-bold text-[#AFDDFF]">
                            {(item.win_probability * 100).toFixed(1)}%
                          </td>
                          <td className="py-3.5 px-4">
                            <StatusBadge status={item.ai_recommendation} type="recommendation" />
                          </td>
                          <td className="py-3.5 px-4 font-bold text-[#9FE6C1]">
                            ₹{Math.max(0, netAdvantage).toLocaleString('en-IN')}
                          </td>
                          <td className="py-3.5 px-4">
                            <span className={`px-2 py-0.5 border text-[10px] font-bold ${priorityTier === 'CRITICAL' ? 'border-[#E68A8A] text-[#E68A8A] bg-[#E68A8A]/10' : priorityTier === 'HIGH' ? 'border-[#F4C46B] text-[#F4C46B] bg-[#F4C46B]/10' : 'border-[#9FE6C1] text-[#9FE6C1] bg-[#9FE6C1]/10'}`}>
                              [{priorityTier}]
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <StatusBadge status={item.review_status} type="review" />
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <button
                              onClick={() => navigate(`/cases/${item.dispute_id}`)}
                              className="px-3 py-1.5 border border-white/20 hover:border-[#AFDDFF] hover:text-[#AFDDFF] text-white font-mono text-[11px] uppercase tracking-wider transition-all"
                            >
                              INSPECT_CASE &rarr;
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              <div className="px-6 py-4 border-t border-white/12 flex items-center justify-between font-mono text-xs bg-black">
                <div className="text-white/40 uppercase tracking-wider text-[11px]">
                  PAGE <span className="text-white font-bold">{page}</span> OF{' '}
                  <span className="text-white font-bold">{totalPages}</span> ({totalCount} CASES TOTAL)
                </div>
                <div className="flex items-center gap-3">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-4 py-1.5 border border-white/20 hover:border-[#AFDDFF] disabled:opacity-30 text-white font-mono text-xs uppercase tracking-wider transition-all"
                  >
                    [ PREV ]
                  </button>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
