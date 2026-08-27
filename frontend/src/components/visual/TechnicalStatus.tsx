import React from 'react';

interface TechnicalStatusProps {
  status: string;
  variant?: 'green' | 'amber' | 'red' | 'ice' | 'muted';
  size?: 'sm' | 'md';
}

export const TechnicalStatus: React.FC<TechnicalStatusProps> = ({ 
  status, 
  variant = 'ice',
  size = 'md'
}) => {
  const upperStatus = status.toUpperCase();

  const getVariantStyles = () => {
    switch (variant) {
      case 'green':
        return 'text-[#9FE6C1] border-[#9FE6C1]/30 bg-[#9FE6C1]/5';
      case 'amber':
        return 'text-[#F4C46B] border-[#F4C46B]/30 bg-[#F4C46B]/5';
      case 'red':
        return 'text-[#E68A8A] border-[#E68A8A]/30 bg-[#E68A8A]/5';
      case 'muted':
        return 'text-white/50 border-white/12 bg-white/5';
      case 'ice':
      default:
        return 'text-[#AFDDFF] border-[#AFDDFF]/30 bg-[#AFDDFF]/5';
    }
  };

  const sizeStyles = size === 'sm' 
    ? 'px-2 py-0.5 text-[9px]' 
    : 'px-2.5 py-1 text-[10px]';

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider border rounded-none ${getVariantStyles()} ${sizeStyles}`}>
      <span className="h-1 w-1 rounded-full bg-current opacity-80" />
      <span>{upperStatus}</span>
    </span>
  );
};
