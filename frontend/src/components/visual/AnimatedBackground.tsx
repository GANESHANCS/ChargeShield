import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { CinematicVideoBackground } from './CinematicVideoBackground';

export type BackgroundVariant =
  | 'hero'
  | 'dashboard'
  | 'queue'
  | 'case'
  | 'model'
  | 'analytics'
  | 'simulation'
  | 'audit'
  | 'login'
  | 'intro';

interface AnimatedBackgroundProps {
  variant?: BackgroundVariant;
}

export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({ variant = 'hero' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Variant video & color configurations strictly matched to prompt specifications
  const variantConfig = {
    hero: {
      bg: '#05070D',
      videoSrc: '/videos/risk-overview.mp4',
      opacity: 0.40,
      blur: '0px',
      overlayIntensity: 0.55,
      primaryGlow: 'rgba(175, 221, 255, 0.12)',
      secondaryGlow: 'rgba(157, 140, 255, 0.08)'
    },
    intro: {
      bg: '#05070D',
      videoSrc: '/videos/intro.mp4',
      opacity: 0.38,
      blur: '0px',
      overlayIntensity: 0.55,
      primaryGlow: 'rgba(175, 221, 255, 0.14)',
      secondaryGlow: 'rgba(157, 140, 255, 0.08)'
    },
    dashboard: {
      bg: '#05070D',
      videoSrc: '/videos/risk-overview.mp4',
      opacity: 0.40,
      blur: '0px',
      overlayIntensity: 0.55,
      primaryGlow: 'rgba(114, 223, 255, 0.14)',
      secondaryGlow: 'rgba(118, 224, 194, 0.08)'
    },
    queue: {
      bg: '#030A13',
      videoSrc: '/videos/review-queue.mp4',
      opacity: 0.35,
      blur: '0px',
      overlayIntensity: 0.60,
      primaryGlow: 'rgba(175, 221, 255, 0.10)',
      secondaryGlow: 'rgba(114, 223, 255, 0.10)'
    },
    case: {
      bg: '#02050A',
      videoSrc: '/videos/case-investigation.mp4',
      opacity: 0.38,
      blur: '0px',
      overlayIntensity: 0.55,
      primaryGlow: 'rgba(157, 140, 255, 0.12)',
      secondaryGlow: 'rgba(175, 221, 255, 0.10)'
    },
    model: {
      bg: '#070612',
      videoSrc: '/videos/model-intelligence.mp4',
      opacity: 0.42,
      blur: '0px',
      overlayIntensity: 0.50,
      primaryGlow: 'rgba(157, 140, 255, 0.16)',
      secondaryGlow: 'rgba(114, 223, 255, 0.08)'
    },
    analytics: {
      bg: '#06100F',
      videoSrc: '/videos/analytics.mp4',
      opacity: 0.38,
      blur: '0px',
      overlayIntensity: 0.58,
      primaryGlow: 'rgba(118, 224, 194, 0.14)',
      secondaryGlow: 'rgba(157, 140, 255, 0.12)'
    },
    simulation: {
      bg: '#05070D',
      videoSrc: '/videos/simulation.mp4',
      opacity: 0.45,
      blur: '0px',
      overlayIntensity: 0.50,
      primaryGlow: 'rgba(244, 196, 107, 0.14)',
      secondaryGlow: 'rgba(175, 221, 255, 0.10)'
    },
    audit: {
      bg: '#05070D',
      videoSrc: '/videos/audit.mp4',
      opacity: 0.32,
      blur: '0px',
      overlayIntensity: 0.65,
      primaryGlow: 'rgba(175, 221, 255, 0.10)',
      secondaryGlow: 'rgba(118, 224, 194, 0.08)'
    },
    login: {
      bg: '#05070D',
      videoSrc: '/videos/login.mp4',
      opacity: 0.40,
      blur: '0px',
      overlayIntensity: 0.55,
      primaryGlow: 'rgba(175, 221, 255, 0.10)',
      secondaryGlow: 'rgba(157, 140, 255, 0.08)'
    }
  }[variant] || {
    bg: '#05070D',
    videoSrc: '/videos/risk-overview.mp4',
    opacity: 0.40,
    blur: '0px',
    overlayIntensity: 0.55,
    primaryGlow: 'rgba(175, 221, 255, 0.12)',
    secondaryGlow: 'rgba(157, 140, 255, 0.08)'
  };

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
    const count = Math.min(Math.floor((width * height) / 28000), 30);
    const particles = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      size: Math.random() * 1.4 + 0.6,
      alpha: Math.random() * 0.25 + 0.08,
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
        ctx.shadowBlur = 4;
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
      {/* 1. Cinematic Video Background */}
      <CinematicVideoBackground
        videoSrc={variantConfig.videoSrc}
        opacity={variantConfig.opacity}
        blur={variantConfig.blur}
        overlayIntensity={variantConfig.overlayIntensity}
      />

      {/* 2. Primary Ambient Radial Glow */}
      <motion.div
        animate={{
          x: [0, 40, -30, 0],
          y: [0, -30, 40, 0],
          scale: [1, 1.15, 0.95, 1],
        }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
        style={{ background: variantConfig.primaryGlow }}
        className="absolute -top-32 -left-32 w-[600px] h-[600px] rounded-full blur-[120px] pointer-events-none"
      />

      {/* 3. Secondary Ambient Radial Glow */}
      <motion.div
        animate={{
          x: [0, -50, 30, 0],
          y: [0, 40, -30, 0],
          scale: [1, 0.9, 1.1, 1],
        }}
        transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut' }}
        style={{ background: variantConfig.secondaryGlow }}
        className="absolute top-1/2 -right-32 w-[700px] h-[700px] rounded-full blur-[140px] pointer-events-none"
      />

      {/* 4. Canvas Floating Particles */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-50 pointer-events-none" />
    </div>
  );
};
