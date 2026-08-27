import React from 'react';

interface SectionLabelProps {
  label: string;
  className?: string;
  badge?: string;
}

export const SectionLabel: React.FC<SectionLabelProps> = ({ label, className = '', badge }) => {
  const cleanLabel = label.startsWith('[') && label.endsWith(']') 
    ? label 
    : `[ ${label.toUpperCase().replace(/\s+/g, '_')} ]`;

  return (
    <div className={`flex items-center gap-3 font-mono text-[11px] tracking-widest text-[#AFDDFF] ${className}`}>
      <span className="font-medium">{cleanLabel}</span>
      {badge && (
        <span className="px-2 py-0.5 text-[9px] bg-[#AFDDFF]/10 text-[#AFDDFF] border border-[#AFDDFF]/25 font-mono uppercase tracking-wider">
          {badge}
        </span>
      )}
    </div>
  );
};
