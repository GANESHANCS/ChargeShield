import React from 'react';

interface ProbabilityGaugeProps {
  probability: number; // 0.0 to 1.0
  threshold?: number; // default 0.29
  recommendation?: string;
}

export const ProbabilityGauge: React.FC<ProbabilityGaugeProps> = ({
  probability,
  threshold = 0.29
}) => {
  const percent = Math.round(probability * 1000) / 10;
  const threshPercent = Math.round(threshold * 100);
  const isAboveThreshold = probability >= threshold;

  return (
    <div className="space-y-3 font-mono">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="text-white/50 uppercase tracking-widest text-[10px]">[ WIN_PROBABILITY ]</span>
          <span className={`text-xl font-light font-mono ${isAboveThreshold ? 'text-[#AFDDFF]' : 'text-[#E68A8A]'}`}>
            {percent}%
          </span>
        </div>
        <div className="text-[11px] text-white/50">
          OPTIMAL THRESHOLD: <span className="text-[#F4C46B]">{threshPercent}%</span>
        </div>
      </div>

      {/* Technical Bar Track */}
      <div className="relative h-2 w-full bg-white/[0.04] border border-white/12 overflow-hidden">
        {/* Filled Bar */}
        <div
          className={`h-full transition-all duration-500 ${
            isAboveThreshold ? 'bg-[#AFDDFF]' : 'bg-[#E68A8A]'
          }`}
          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
        />

        {/* Threshold Divider Marker */}
        <div
          className="absolute top-0 bottom-0 w-[2px] bg-[#F4C46B] z-10"
          style={{ left: `${threshPercent}%` }}
          title={`Cost-Optimal Threshold: ${threshPercent}%`}
        />
      </div>

      <div className="flex justify-between text-[9px] text-white/40 uppercase tracking-wider">
        <span>0% LOW_PROBABILITY</span>
        <span className="text-[#F4C46B]">▲ OPTIMAL COST THRESHOLD ({threshPercent}%)</span>
        <span>100% HIGH_PROBABILITY</span>
      </div>
    </div>
  );
};
