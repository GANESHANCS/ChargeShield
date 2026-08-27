import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const upper = status.toUpperCase();

  let style = 'bg-white/5 text-white/70 border-white/12';
  let dotColor = 'bg-white/40';
  let label = status;

  // Review Statuses
  if (upper === 'PENDING_REVIEW') {
    style = 'bg-[#AFDDFF]/5 text-[#AFDDFF] border-[#AFDDFF]/30';
    dotColor = 'bg-[#AFDDFF]';
    label = 'PENDING_REVIEW';
  } else if (upper === 'IN_REVIEW') {
    style = 'bg-[#AFDDFF]/10 text-[#AFDDFF] border-[#AFDDFF]/40';
    dotColor = 'bg-[#AFDDFF]';
    label = 'IN_REVIEW';
  } else if (upper === 'DECIDED') {
    style = 'bg-[#9FE6C1]/10 text-[#9FE6C1] border-[#9FE6C1]/30';
    dotColor = 'bg-[#9FE6C1]';
    label = 'DECIDED';
  } else if (upper === 'ESCALATED') {
    style = 'bg-purple-500/10 text-purple-300 border-purple-500/30';
    dotColor = 'bg-purple-400';
    label = 'ESCALATED';
  }

  // Evidence Verification Statuses
  else if (upper === 'VERIFIED') {
    style = 'bg-[#9FE6C1]/10 text-[#9FE6C1] border-[#9FE6C1]/30';
    dotColor = 'bg-[#9FE6C1]';
    label = '● VERIFIED';
  } else if (upper === 'MISMATCH' || upper === 'MISMATCHED') {
    style = 'bg-[#F4C46B]/10 text-[#F4C46B] border-[#F4C46B]/30';
    dotColor = 'bg-[#F4C46B]';
    label = '▲ MISMATCHED';
  } else if (upper === 'MISSING_SOURCE' || upper === 'UNSUPPORTED' || upper === 'UNVERIFIABLE' || upper === 'UNVERIFIED') {
    style = 'bg-white/5 text-white/50 border-white/15';
    dotColor = 'bg-white/40';
    label = upper === 'MISSING_SOURCE' ? '✖ MISSING_SOURCE' : upper === 'UNVERIFIABLE' ? '✖ UNVERIFIABLE' : `● ${upper}`;
  }

  // Recommendation Statuses
  else if (upper === 'CONTEST') {
    style = 'bg-[#9FE6C1]/10 text-[#9FE6C1] border-[#9FE6C1]/30';
    dotColor = 'bg-[#9FE6C1]';
    label = 'CONTEST';
  } else if (upper === 'DO_NOT_CONTEST') {
    style = 'bg-[#E68A8A]/10 text-[#E68A8A] border-[#E68A8A]/30';
    dotColor = 'bg-[#E68A8A]';
    label = 'DO_NOT_CONTEST';
  } else if (upper === 'ESCALATE') {
    style = 'bg-purple-500/10 text-purple-300 border-purple-500/30';
    dotColor = 'bg-purple-400';
    label = 'ESCALATE';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono tracking-wider uppercase border rounded-none ${style}`}>
      {!label.startsWith('●') && !label.startsWith('▲') && !label.startsWith('✖') && (
        <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
      )}
      <span>{label}</span>
    </span>
  );
};
