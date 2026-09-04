import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export const NavigationRail: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('01');
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);

      // Section scroll tracking on landing page
      const sections = ['hero', 'risk-engine', 'intelligence', 'ai-human', 'cases', 'pipeline', 'analytics', 'audit'];
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 200 && rect.bottom >= 200) {
            if (sectionId === 'hero') setActiveSection('01');
            if (sectionId === 'risk-engine') setActiveSection('02');
            if (sectionId === 'intelligence') setActiveSection('03');
            if (sectionId === 'cases') setActiveSection('04');
            if (sectionId === 'analytics') setActiveSection('05');
            if (sectionId === 'audit') setActiveSection('06');
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const allNavItems = [
    { label: '01 RISK_OVERVIEW', path: '/dashboard', accent: '#00F0FF', allowedRoles: ['ADMIN', 'ANALYST', 'REVIEWER', 'AUDITOR'] },
    { label: '02 REVIEW_QUEUE', path: '/queue', accent: '#F4C46B', allowedRoles: ['ADMIN', 'ANALYST', 'REVIEWER'] },
    { label: '03 CASES', path: '/cases/DSP_000001', accent: '#00E5FF', allowedRoles: ['ADMIN', 'ANALYST', 'REVIEWER', 'AUDITOR'] },
    { label: '04 MODEL', path: '/model', accent: '#A78BFA', allowedRoles: ['ADMIN', 'ANALYST'] },
    { label: '05 ANALYTICS', path: '/analytics', accent: '#00F5D4', allowedRoles: ['ADMIN', 'ANALYST', 'AUDITOR'] },
    { label: '06 AUDIT', path: '/audit', accent: '#CBD5E1', allowedRoles: ['ADMIN', 'ANALYST', 'REVIEWER', 'AUDITOR'] },
    { label: '07 SIMULATION', path: '/simulation', accent: '#E879F9', allowedRoles: ['ADMIN', 'ANALYST'] },
  ];

  // Role-Aware Navigation Filtering
  const userRole = user?.role?.toUpperCase() || 'REVIEWER';
  const navItems = allNavItems.filter((item) => {
    if (userRole === 'ADMIN') return true;
    return item.allowedRoles.includes(userRole);
  });

  const handleNavClick = (path: string) => {
    setMobileMenuOpen(false);
    navigate(path);
  };

  return (
    <>
      <header
        className={`sticky top-0 z-40 w-full backdrop-blur-md transition-all duration-300 border-b ${
          scrolled ? 'bg-[#050607]/95 border-white/12 py-3.5' : 'bg-[#050607]/75 border-white/10 py-4'
        }`}
      >
        <div className="max-w-[1600px] mx-auto px-[20px] md:px-[35px] flex items-center justify-between font-mono text-xs">
          {/* Logo & Brand */}
          <div
            onClick={() => navigate('/dashboard')}
            className="cursor-pointer flex items-center gap-3 text-white group"
          >
            <span className="h-1.5 w-1.5 bg-[#AFDDFF] group-hover:animate-ping" />
            <span className="font-display font-light text-sm tracking-wider text-white group-hover:text-[#AFDDFF] transition-colors">
              CHARGESHIELD <span className="text-[#AFDDFF] font-mono text-xs">// {activeSection}</span>
            </span>
          </div>

          {/* Navigation Links Desktop */}
          <nav className="hidden lg:flex items-center gap-8">
            {navItems.map((item) => {
              const isActive =
                item.path === '/dashboard'
                  ? location.pathname === '/dashboard' || location.pathname === '/'
                  : item.path.startsWith('/cases')
                  ? location.pathname.startsWith('/cases')
                  : location.pathname === item.path;

              return (
                <button
                  key={item.label}
                  onClick={() => handleNavClick(item.path)}
                  className={`transition-colors uppercase tracking-widest text-[11px] font-mono relative py-1 ${
                    isActive ? 'font-bold' : 'text-white/60 hover:text-white'
                  }`}
                  style={{ color: isActive ? item.accent : undefined }}
                >
                  {item.label}
                  {isActive && (
                    <motion.div
                      layoutId="activeNavIndicator"
                      className="absolute bottom-0 left-0 right-0 h-[1.5px]"
                      style={{ backgroundColor: item.accent }}
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </nav>

          {/* System Ticker Indicator & User Identity */}
          <div className="hidden sm:flex items-center gap-3 text-[10px]">
            <div className="flex items-center gap-2 border border-white/12 px-2.5 py-1 bg-black">
              <span className="h-1.5 w-1.5 rounded-full bg-[#AFDDFF] animate-pulse" />
              <span className="text-white/40">ENV:</span>
              <span className="text-[#AFDDFF] font-bold">[ SIMULATION ]</span>
            </div>
            
            {user ? (
              <div className="flex items-center gap-2 border border-white/15 bg-white/5 px-2.5 py-1">
                <span className="text-white/60">{user.username}</span>
                <span className={`px-1.5 py-0.5 text-[9px] font-bold border ${
                  user.role === 'ADMIN' ? 'border-[#AFDDFF] text-[#AFDDFF]' :
                  user.role === 'ANALYST' ? 'border-[#F4C46B] text-[#F4C46B]' :
                  user.role === 'AUDITOR' ? 'border-[#D8B4FE] text-[#D8B4FE]' :
                  'border-[#9FE6C1] text-[#9FE6C1]'
                }`}>
                  {user.role}
                </span>
                <button
                  onClick={logout}
                  className="ml-1 text-white/40 hover:text-[#E68A8A] transition-colors uppercase"
                  title="Logout Session"
                >
                  [ LOGOUT ]
                </button>
              </div>
            ) : (
              <button
                onClick={() => navigate('/login')}
                className="border border-[#AFDDFF]/40 bg-[#AFDDFF]/10 text-[#AFDDFF] hover:bg-[#AFDDFF] hover:text-black transition-colors px-3 py-1 font-bold tracking-wider uppercase"
              >
                [ LOGIN ]
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden text-white border border-white/20 p-2 uppercase font-mono text-[11px] tracking-wider hover:border-[#AFDDFF]"
          >
            {mobileMenuOpen ? '[ CLOSE ]' : '[ MENU ]'}
          </button>
        </div>
      </header>

      {/* Cinematic Full-Screen Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-50 bg-black/95 backdrop-blur-xl flex flex-col justify-between p-8 font-mono"
          >
            <div className="flex items-center justify-between border-b border-white/12 pb-6">
              <div className="font-bold text-white text-base">CHARGESHIELD // MENU</div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="text-white/60 hover:text-white text-xs border border-white/20 px-3 py-1.5 uppercase"
              >
                [ CLOSE ]
              </button>
            </div>

            <div className="space-y-6 my-auto">
              {navItems.map((item, idx) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: -30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.08 }}
                >
                  <button
                    onClick={() => handleNavClick(item.path)}
                    className="text-2xl font-display font-light text-white hover:text-[#AFDDFF] transition-colors tracking-wide text-left uppercase"
                  >
                    {item.label}
                  </button>
                </motion.div>
              ))}
            </div>

            <div className="border-t border-white/12 pt-6 text-xs text-white/40 space-y-2">
              <div>CHARGESHIELD // AI RISK INTELLIGENCE</div>
              <div className="text-[#9FE6C1] font-bold">SYSTEM STATUS: ONLINE</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
