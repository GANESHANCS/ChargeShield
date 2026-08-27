import React from 'react';

export const GridBackground: React.FC = () => {
  return (
    <div 
      aria-hidden="true" 
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden select-none"
    >
      {/* Base Subtle Grid Pattern */}
      <div 
        className="absolute inset-0" 
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '120px 120px',
        }}
      />

      {/* Selected Intersection "+" Markers */}
      <div className="absolute inset-0" style={{ backgroundSize: '240px 240px' }}>
        {[
          { top: '120px', left: '120px' },
          { top: '120px', left: '600px' },
          { top: '120px', left: '1080px' },
          { top: '360px', left: '360px' },
          { top: '360px', left: '840px' },
          { top: '600px', left: '120px' },
          { top: '600px', left: '600px' },
          { top: '600px', left: '1080px' },
          { top: '840px', left: '360px' },
          { top: '840px', left: '840px' },
        ].map((pos, idx) => (
          <div
            key={idx}
            className="absolute text-[10px] font-mono text-white/20 -translate-x-1/2 -translate-y-1/2 font-light"
            style={{ top: pos.top, left: pos.left }}
          >
            +
          </div>
        ))}
      </div>

      {/* Subtle Radial Gradient Vignette */}
      <div 
        className="absolute inset-0" 
        style={{
          background: 'radial-gradient(circle at 50% 30%, transparent 40%, rgba(0, 0, 0, 0.8) 100%)'
        }}
      />
    </div>
  );
};
