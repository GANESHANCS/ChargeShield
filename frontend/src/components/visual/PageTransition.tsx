import React from 'react';
import { motion } from 'framer-motion';

interface PageTransitionProps {
  children: React.ReactNode;
}

export const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.99 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -12, scale: 0.99 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="w-full relative"
    >
      {/* Top Sweeping Accent Line */}
      <motion.div
        initial={{ x: '-100%' }}
        animate={{ x: '100%' }}
        transition={{ duration: 0.8, ease: 'easeInOut' }}
        className="fixed top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#AFDDFF] to-transparent z-50 pointer-events-none"
      />
      {children}
    </motion.div>
  );
};
