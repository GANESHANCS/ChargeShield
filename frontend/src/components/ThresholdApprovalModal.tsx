import React, { useState } from 'react';
import { api } from '../services/api';

interface ThresholdApprovalModalProps {
  currentThreshold: number;
  recommendedThreshold: number;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ThresholdApprovalModal: React.FC<ThresholdApprovalModalProps> = ({
  currentThreshold,
  recommendedThreshold,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [proposedThreshold, setProposedThreshold] = useState<number>(recommendedThreshold || 0.35);
  const [reason, setReason] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason || reason.trim().length < 10) {
      setError('A comprehensive analytical justification (at least 10 characters) is required for Admin threshold approval.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await api.approveModelThreshold({
        proposed_threshold: proposedThreshold,
        reason: reason.trim(),
        evidence_metrics: {
          previous_threshold: currentThreshold,
          recommended_threshold: recommendedThreshold,
          eval_horizon: "30D"
        }
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to approve model threshold update.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-lumen-fade-in">
      <div className="w-full max-w-lg bg-[#0D0B1F] border border-[#AFDDFF]/40 p-6 space-y-6 shadow-2xl font-mono text-xs">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/12 pb-4">
          <div>
            <span className="text-[10px] text-[#AFDDFF] uppercase tracking-widest">[ ADMIN GOVERNANCE WORKFLOW ]</span>
            <h3 className="text-lg font-display font-semibold text-white mt-0.5">
              Approve Model Threshold Change
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white text-lg font-bold px-2 py-1"
          >
            ✕
          </button>
        </div>

        {/* Warning Banner */}
        <div className="p-3 border border-purple-400/40 bg-purple-500/10 text-purple-200 space-y-1 text-[11px]">
          <div className="font-bold uppercase tracking-wider">ADMIN GOVERNANCE REQUIREMENT:</div>
          <div>Threshold changes affect live fraud classification rules. Autonomous threshold changes are strictly disabled. An immutable audit record will be logged.</div>
        </div>

        {error && (
          <div className="p-3 border border-[#E68A8A]/40 bg-[#E68A8A]/10 text-[#E68A8A]">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Threshold Comparison */}
          <div className="grid grid-cols-2 gap-4 p-4 border border-white/12 bg-black">
            <div className="space-y-1">
              <div className="text-white/40 text-[10px] uppercase">CURRENT THRESHOLD</div>
              <div className="text-2xl font-bold text-white">{currentThreshold}</div>
            </div>
            <div className="space-y-1">
              <div className="text-[#AFDDFF] text-[10px] uppercase font-bold">NEW PROPOSED THRESHOLD</div>
              <input
                type="number"
                step="0.01"
                min="0.05"
                max="0.95"
                value={proposedThreshold}
                onChange={(e) => setProposedThreshold(parseFloat(e.target.value))}
                className="w-full bg-black border border-[#AFDDFF]/50 p-1 text-2xl font-bold text-[#AFDDFF] focus:outline-none"
              />
            </div>
          </div>

          {/* Reason */}
          <div className="space-y-1">
            <label className="block text-white/60 text-[10px] uppercase">ANALYTICAL JUSTIFICATION & BUSINESS REASONING *</label>
            <textarea
              rows={4}
              placeholder="e.g. Empirical evaluation across 30D production outcome ground-truth confirms optimal net financial recovery at 0.35 threshold."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-black border border-white/12 p-2 text-white font-mono text-xs focus:border-[#AFDDFF] focus:outline-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/12">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-white/20 text-white/60 hover:text-white hover:border-white/40 uppercase tracking-widest text-[10px]"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 border border-[#AFDDFF] bg-[#AFDDFF]/20 text-[#AFDDFF] font-bold hover:bg-[#AFDDFF]/30 uppercase tracking-widest text-[10px] disabled:opacity-50"
            >
              {submitting ? 'RECORDING GOVERNANCE AUDIT...' : 'AUTHORIZE & DEPLOY THRESHOLD'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
