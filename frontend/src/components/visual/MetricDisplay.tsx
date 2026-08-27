import React from 'react';

interface MetricDisplayProps {
  label: string;
  value: string | number;
  subtext?: string;
  accentColor?: 'ice' | 'white' | 'green' | 'amber' | 'purple';
  large?: boolean;
}

export const MetricDisplay: React.FC<MetricDisplayProps> = ({
  label,
  value,
  subtext,
  accentColor = 'white',
  large = false,
}) => {
  const getTextColor = () => {
    switch (accentColor) {
      case 'ice': return 'text-[#AFDDFF]';
      case 'green': return 'text-[#9FE6C1]';
      case 'amber': return 'text-[#F4C46B]';
      case 'purple': return 'text-purple-300';
      case 'white':
      default: return 'text-white';
    }
  };

  return (
    <div className="space-y-1">
      <div className="text-[10px] font-mono text-white/50 uppercase tracking-widest">
        {label}
      </div>
      <div className={`font-mono font-light tracking-tight ${getTextColor()} ${large ? 'text-3xl lg:text-4xl' : 'text-2xl'}`}>
        {value}
      </div>
      {subtext && (
        <div className="text-[11px] font-mono text-white/40">
          {subtext}
        </div>
      )}
    </div>
  );
};
