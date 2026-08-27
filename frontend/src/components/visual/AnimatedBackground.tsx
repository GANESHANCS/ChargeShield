import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

export type BackgroundVariant = 'hero' | 'dashboard' | 'queue' | 'case' | 'model' | 'analytics' | 'audit';

interface AnimatedBackgroundProps {
  variant?: BackgroundVariant;
}

export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({ variant = 'hero' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Variant color configurations
  const variantConfig = {
    hero: { bg: '#05070D', primaryGlow: 'rgba(175, 221, 255, 0.12)', secondaryGlow: 'rgba(157, 140, 255, 0.08)' },
    dashboard: { bg: '#05070D', primaryGlow: 'rgba(114, 223, 255, 0.14)', secondaryGlow: 'rgba(118, 224, 194, 0.08)' },
    queue: { bg: '#030A13', primaryGlow: 'rgba(175, 221, 255, 0.10)', secondaryGlow: 'rgba(114, 223, 255, 0.10)' },
    case: { bg: '#02050A', primaryGlow: 'rgba(157, 140, 255, 0.12)', secondaryGlow: 'rgba(175, 221, 255, 0.10)' },
    model: { bg: '#070612', primaryGlow: 'rgba(157, 140, 255, 0.16)', secondaryGlow: 'rgba(114, 223, 255, 0.08)' },
    analytics: { bg: '#06100F', primaryGlow: 'rgba(118, 224, 194, 0.14)', secondaryGlow: 'rgba(157, 140, 255, 0.12)' },
    audit: { bg: '#05070D', primaryGlow: 'rgba(175, 221, 255, 0.10)', secondaryGlow: 'rgba(118, 224, 194, 0.08)' },
  }[variant];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particle setup
    const count = Math.min(Math.floor((width * height) / 24000), 40);
    const particles = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 1.5 + 0.8,
      alpha: Math.random() * 0.3 + 0.1,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Render subtle particles
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(175, 221, 255, ${p.alpha})`;
        ctx.shadowBlur = 6;
        ctx.shadowColor = '#AFDDFF';
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [variant]);

  return (
    <div
      style={{ backgroundColor: variantConfig.bg }}
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden transition-colors duration-1000"
    >
      {/* Primary Radial Glow Orb 1 */}
      <motion.div
        animate={{
          x: [0, 40, -30, 0],
          y: [0, -30, 40, 0],
          scale: [1, 1.15, 0.95, 1],
        }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
        style={{ background: variantConfig.primaryGlow }}
        className="absolute -top-32 -left-32 w-[600px] h-[600px] rounded-full blur-[120px]"
      />

      {/* Secondary Radial Glow Orb 2 */}
      <motion.div
        animate={{
          x: [0, -50, 30, 0],
          y: [0, 40, -30, 0],
          scale: [1, 0.9, 1.1, 1],
        }}
        transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut' }}
        style={{ background: variantConfig.secondaryGlow }}
        className="absolute top-1/2 -right-32 w-[700px] h-[700px] rounded-full blur-[140px]"
      />

      {/* Soft Bottom Accent Orb */}
      <div
        style={{ background: 'rgba(114, 223, 255, 0.05)' }}
        className="absolute -bottom-40 left-1/3 w-[800px] h-[500px] rounded-full blur-[150px]"
      />

      {/* Subtle LŪMEN Technical Backdrop Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] opacity-70" />

      {/* Canvas Floating Particles */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-60" />
    </div>
  );
};
