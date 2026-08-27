import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

interface EditorialImageHeroProps {
  imageSrc: string;
  category: string;
  titleLines: string[];
  subtitle: string;
  metadata?: { label: string; value: string }[];
  children?: React.ReactNode;
}

export const EditorialImageHero: React.FC<EditorialImageHeroProps> = ({
  imageSrc,
  category,
  titleLines,
  subtitle,
  metadata = [],
  children,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  });

  // Layered differential parallax speeds
  const imageY = useTransform(scrollYProgress, [0, 1], ['0%', '20%']);
  const imageScale = useTransform(scrollYProgress, [0, 1], [1.0, 1.08]);
  const textY = useTransform(scrollYProgress, [0, 1], ['0%', '35%']);
  const textOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);
  const gridY = useTransform(scrollYProgress, [0, 1], ['0%', '10%']);

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden border-b border-white/12 bg-[#050607] min-h-[480px] lg:min-h-[580px] flex items-center select-none"
    >
      {/* Layer 1: Background Base Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#050607] via-[#080B10] to-[#050607] z-0" />

      {/* Layer 2: Technical Grid Texture (Scroll Speed: 0.10x) */}
      <motion.div
        style={{ y: gridY }}
        className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:80px_80px] opacity-40 z-[1] pointer-events-none"
      />

      {/* Layer 3: Editorial Art Image Composition (Scroll Speed: 0.25x) */}
      <div className="absolute inset-0 z-[2] overflow-hidden flex items-center justify-end">
        <motion.div
          style={{ y: imageY, scale: imageScale }}
          className="relative w-full h-full md:w-[75%] lg:w-[65%] opacity-40 lg:opacity-60 mix-blend-luminosity filter contrast-125 transition-all duration-700"
        >
          <img
            src={imageSrc}
            alt={titleLines.join(' ')}
            className="w-full h-full object-cover object-center"
          />
          {/* Subtle gradient vignette to blend image with typography */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#050607] via-[#050607]/70 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#050607] via-transparent to-[#050607]/80" />
        </motion.div>
      </div>

      {/* Layer 4: Soft Accent Atmospheric Light */}
      <div className="absolute -top-40 -left-20 w-[600px] h-[600px] bg-[#AFDDFF]/5 rounded-full blur-[140px] pointer-events-none z-[3]" />

      {/* Layer 5: Editorial Content & Typography (Scroll Speed: 0.35x) */}
      <motion.div
        style={{ y: textY, opacity: textOpacity }}
        className="relative z-[10] max-w-[1600px] w-full mx-auto px-[20px] md:px-[35px] py-12 lg:py-16 flex flex-col justify-between"
      >
        {/* Category Metadata Header */}
        <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.25em] text-[#AFDDFF] mb-6">
          <span className="h-1.5 w-1.5 bg-[#AFDDFF]" />
          <span>[ {category} ]</span>
          <span className="text-white/30">&bull;</span>
          <span className="text-white/50">CHARGESHIELD INTEL SYSTEM</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          {/* Stacked Large Editorial Typography */}
          <div className="lg:col-span-8 space-y-2">
            {titleLines.map((line, idx) => (
              <motion.h1
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: idx * 0.12, ease: [0.16, 1, 0.3, 1] }}
                className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extralight font-display tracking-tight text-white uppercase leading-[0.92]"
              >
                {line}
              </motion.h1>
            ))}
            <motion.p
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: titleLines.length * 0.12 }}
              className="text-xs sm:text-sm font-mono text-white/60 max-w-xl pt-4 leading-relaxed tracking-wide"
            >
              {subtitle}
            </motion.p>
          </div>

          {/* Right Column: Metadata Strip or Extra Visual Action */}
          <div className="lg:col-span-4 flex flex-col justify-end space-y-4 font-mono text-xs border-l border-white/12 pl-6 lg:pl-8">
            {metadata.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="text-white/40 uppercase tracking-widest text-[10px]">{item.label}</span>
                <span className="text-white font-medium text-[11px]">{item.value}</span>
              </div>
            ))}
            {children && <div className="pt-2">{children}</div>}
          </div>
        </div>
      </motion.div>
    </div>
  );
};
