import React, { useEffect, useRef, useState } from 'react';

export interface CinematicVideoBackgroundProps {
  videoSrc: string;
  poster?: string;
  opacity?: number; // 0.0 to 1.0
  blur?: string; // e.g. "0px", "1px", "2px"
  overlayIntensity?: number; // 0.0 to 1.0
  className?: string;
}

export const CinematicVideoBackground: React.FC<CinematicVideoBackgroundProps> = ({
  videoSrc,
  poster,
  opacity = 0.25,
  blur = '0px',
  overlayIntensity = 0.60,
  className = ''
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);
  const [isMobile, setIsMobile] = useState<boolean>(false);

  // 1. Detect prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      mediaQuery.addListener(handleChange);
    }

    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        mediaQuery.removeListener(handleChange);
      }
    };
  }, []);

  // 2. Detect mobile viewport (<768px)
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 3. Pause video when page is hidden to conserve system resources
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!videoRef.current) return;
      if (document.hidden) {
        videoRef.current.pause();
      } else if (!prefersReducedMotion) {
        videoRef.current.play().catch(() => {});
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [prefersReducedMotion]);

  // 4. Race-safe playback effect: attempt play without triggering load() or play loops
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (prefersReducedMotion) {
      video.pause();
      return;
    }

    let isSubscribed = true;

    const playVideo = () => {
      if (!isSubscribed || !video) return;
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          // Gracefully swallow AbortError or autoplay restriction without breaking state
          if (err.name !== 'AbortError') {
            console.warn('CinematicVideoBackground playback info:', err.message);
          }
        });
      }
    };

    if (video.readyState >= 2) {
      playVideo();
    } else {
      video.addEventListener('canplay', playVideo, { once: true });
      video.addEventListener('loadeddata', playVideo, { once: true });
    }

    // Direct initial attempt
    playVideo();

    return () => {
      isSubscribed = false;
      video.removeEventListener('canplay', playVideo);
      video.removeEventListener('loadeddata', playVideo);
    };
  }, [videoSrc, prefersReducedMotion]);

  const effectiveOpacity = isMobile ? opacity * 0.6 : opacity;

  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 z-0 overflow-hidden pointer-events-none select-none bg-transparent ${className}`}
    >
      {/* 1. Video Layer */}
      {!prefersReducedMotion && (
        <video
          ref={videoRef}
          key={videoSrc}
          src={videoSrc}
          autoPlay
          loop
          muted
          playsInline
          poster={poster}
          className="absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ease-out pointer-events-none"
          style={{
            opacity: effectiveOpacity,
            filter: blur !== '0px' ? `blur(${blur})` : 'none'
          }}
        />
      )}

      {/* 2. Visual Overlay Gradients (Ensures LŪMEN dark graphite readability) */}
      <div
        className="absolute inset-0 transition-opacity duration-500 pointer-events-none"
        style={{
          background: `
            radial-gradient(circle at 50% 30%, rgba(5, 7, 13, ${overlayIntensity * 0.3}) 0%, rgba(5, 7, 13, ${overlayIntensity * 0.6}) 100%),
            linear-gradient(to bottom, rgba(5, 7, 13, ${overlayIntensity * 0.5}) 0%, rgba(5, 7, 13, ${overlayIntensity * 0.3}) 50%, rgba(5, 7, 13, ${overlayIntensity * 0.65}) 100%)
          `
        }}
      />

      {/* 3. Subtle LŪMEN Grid Architectural Accent */}
      <div
        className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:6rem_6rem] opacity-30 pointer-events-none"
      />
    </div>
  );
};
