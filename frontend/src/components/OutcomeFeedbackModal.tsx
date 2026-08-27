import React, { useState } from 'react';
import { api } from '../services/api';

interface OutcomeFeedbackModalProps {
  disputeId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const OutcomeFeedbackModal: React.FC<OutcomeFeedbackModalProps> = ({
  disputeId,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [actualOutcome, setActualOutcome] = useState<'WON' | 'LOST' | 'EXPIRED'>('WON');
  const [financialRecovery, setFinancialRecovery] = useState<string>('');
  const [justification, setJustification] = useState<string>('');
  const [resolutionTimestamp, setResolutionTimestamp] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!justification || justification.trim().length < 5) {
      setError('A justification of at least 5 characters is required for model outcome governance.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const parsedAmount = financialRecovery ? parseFloat(financialRecovery) : null;

      await api.recordOutcome({
        dispute_id: disputeId,
        actual_outcome: actualOutcome,
        resolution_timestamp: new Date(resolutionTimestamp).toISOString(),
        financial_recovery_amount: parsedAmount,
        justification: justification.trim()
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to record dispute outcome label');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-lumen-fade-in">
      <div className="w-full max-w-lg bg-[#0D0B1F] border border-white/20 p-6 space-y-6 shadow-2xl font-mono text-xs">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/12 pb-4">
          <div>
            <span className="text-[10px] text-[#AFDDFF] uppercase tracking-widest">[ PHASE 12 OUTCOME FEEDBACK ]</span>
            <h3 className="text-lg font-display font-semibold text-white mt-0.5">
              Record Ground-Truth Outcome ({disputeId})
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
        <div className="p-3 border border-[#F4C46B]/40 bg-[#F4C46B]/5 text-[#F4C46B] space-y-1 text-[11px]">
          <div className="font-bold uppercase tracking-wider">GOVERNANCE RULE:</div>
          <div>Ground-truth outcome labels are written to an immutable audit trail. Simulation cases are strictly rejected.</div>
        </div>

        {error && (
          <div className="p-3 border border-[#E68A8A]/40 bg-[#E68A8A]/10 text-[#E68A8A]">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Actual Outcome */}
          <div className="space-y-2">
            <label className="block text-white/60 text-[10px] uppercase">ACTUAL DISPUTE OUTCOME *</label>
            <div className="grid grid-cols-3 gap-2">
              {(['WON', 'LOST', 'EXPIRED'] as const).map((outcome) => (
                <button
                  type="button"
                  key={outcome}
                  onClick={() => setActualOutcome(outcome)}
                  className={`py-2 px-3 border font-bold text-center transition-all ${
                    actualOutcome === outcome
                      ? outcome === 'WON'
                        ? 'border-[#9FE6C1] bg-[#9FE6C1]/20 text-[#9FE6C1]'
                        : outcome === 'LOST'
                        ? 'border-[#E68A8A] bg-[#E68A8A]/20 text-[#E68A8A]'
                        : 'border-[#F4C46B] bg-[#F4C46B]/20 text-[#F4C46B]'
                      : 'border-white/12 bg-black text-white/50 hover:border-white/30'
                  }`}
                >
                  {outcome}
                </button>
              ))}
            </div>
          </div>

          {/* Resolution Date */}
          <div className="space-y-1">
            <label className="block text-white/60 text-[10px] uppercase">RESOLUTION DATE</label>
            <input
              type="date"
              value={resolutionTimestamp}
              onChange={(e) => setResolutionTimestamp(e.target.value)}
              className="w-full bg-black border border-white/12 p-2 text-white font-mono text-xs focus:border-[#AFDDFF] focus:outline-none"
            />
          </div>

          {/* Financial Recovery Amount */}
          <div className="space-y-1">
            <label className="block text-white/60 text-[10px] uppercase">
              ACTUAL FINANCIAL RECOVERY AMOUNT (INR)
            </label>
            <input
              type="number"
              step="0.01"
              placeholder="e.g. 1500.00 (Leave empty if unavailable)"
              value={financialRecovery}
              onChange={(e) => setFinancialRecovery(e.target.value)}
              className="w-full bg-black border border-white/12 p-2 text-white font-mono text-xs focus:border-[#AFDDFF] focus:outline-none"
            />
            <div className="text-[10px] text-white/40">
              {financialRecovery ? 'Status: EXPLICIT_RECOVERY' : 'Status: INSUFFICIENT_DATA (No financial estimation will be inferred)'}
            </div>
          </div>

          {/* Justification */}
          <div className="space-y-1">
            <label className="block text-white/60 text-[10px] uppercase">AUDIT JUSTIFICATION & REASONING *</label>
            <textarea
              rows={3}
              placeholder="e.g. Bank dispute decision letter received. Acquirer confirmed chargeback reversal."
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
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
              className="px-5 py-2 border border-[#9FE6C1] bg-[#9FE6C1]/20 text-[#9FE6C1] font-bold hover:bg-[#9FE6C1]/30 uppercase tracking-widest text-[10px] disabled:opacity-50"
            >
              {submitting ? 'RECORDING AUDIT...' : 'COMMIT OUTCOME LABEL'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
