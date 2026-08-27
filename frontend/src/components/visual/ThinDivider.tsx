import React from 'react';

interface ThinDividerProps {
  className?: string;
  vertical?: boolean;
}

export const ThinDivider: React.FC<ThinDividerProps> = ({ className = '', vertical = false }) => {
  if (vertical) {
    return <div className={`w-[1px] bg-white/12 self-stretch ${className}`} />;
  }
  return <div className={`h-[1px] w-full bg-white/12 ${className}`} />;
};
