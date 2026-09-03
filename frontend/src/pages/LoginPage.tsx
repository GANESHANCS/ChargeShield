import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { AnimatedBackground } from '../components/visual/AnimatedBackground';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please provide both username/email and password.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg = err?.message || 'Authentication failed. Please check your credentials.';
      setError(typeof msg === 'string' ? msg : 'Authentication failed. Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (roleUsername: string) => {
    setError(null);
    setUsername(roleUsername);
    setPassword('AdminPass123!');
  };

  return (
    <div className="min-h-screen w-full bg-transparent text-white font-mono flex flex-col justify-between p-6 md:p-12 relative overflow-hidden select-none">
      <AnimatedBackground variant="login" />
      {/* Background Architectural Elements */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-[#AFDDFF]/5 blur-[120px] rounded-full pointer-events-none" />

      {/* Header Bar */}
      <header className="relative z-10 flex items-center justify-between border-b border-white/10 pb-6 max-w-6xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 bg-[#AFDDFF] animate-pulse" />
          <span className="font-display text-lg tracking-wider text-white">CHARGESHIELD</span>
          <span className="text-white/40 text-xs">// RISK OPERATIONS PLATFORM</span>
        </div>
        <div className="text-[10px] text-white/40 tracking-widest uppercase border border-white/12 px-3 py-1">
          [ AUTHENTICATION GATEWAY ]
        </div>
      </header>

      {/* Main Login Card Container */}
      <main className="relative z-10 my-auto max-w-md w-full mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="border border-white/15 bg-black/80 backdrop-blur-xl p-8 shadow-2xl relative"
        >
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#AFDDFF] to-transparent" />

          <div className="mb-8">
            <div className="text-[10px] text-[#AFDDFF] font-bold tracking-widest uppercase mb-1">
              [ SYSTEM ACCESS ]
            </div>
            <h1 className="text-2xl font-display font-light text-white tracking-wide">
              INVESTIGATOR AUTHORIZATION
            </h1>
            <p className="text-xs text-white/50 mt-2 leading-relaxed">
              Authenticate using your institutional credentials to access decision workflows, SHAP model traces, and audit logs.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 border border-[#E68A8A]/40 bg-[#E68A8A]/10 text-[#E68A8A] text-xs leading-relaxed flex items-start gap-2">
              <span className="font-bold">[ ERROR ]</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-[10px] text-white/60 uppercase tracking-widest mb-2">
                USERNAME OR EMAIL
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. reviewer or admin"
                className="w-full bg-white/5 border border-white/15 px-4 py-3 text-sm text-white focus:outline-none focus:border-[#AFDDFF] transition-colors placeholder:text-white/20"
                autoComplete="username"
              />
            </div>

            <div>
              <label className="block text-[10px] text-white/60 uppercase tracking-widest mb-2">
                SECURITY PASSWORD
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
                className="w-full bg-white/5 border border-white/15 px-4 py-3 text-sm text-white focus:outline-none focus:border-[#AFDDFF] transition-colors placeholder:text-white/20"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-white text-black font-bold text-xs tracking-widest uppercase hover:bg-[#AFDDFF] transition-colors flex items-center justify-center gap-2"
            >
              {loading ? '[ AUTHENTICATING... ]' : '[ AUTHENTICATE SYSTEM SESSION ]'}
            </button>
          </form>

          {/* Development Quick-Fill Seed Account Buttons */}
          <div className="mt-8 border-t border-white/10 pt-6">
            <div className="text-[9px] text-white/40 tracking-widest uppercase mb-3 text-center">
              DEMO / DEV QUICK ACCESSIBLE ROLES
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <button
                type="button"
                onClick={() => handleQuickFill('admin')}
                className="p-2 border border-white/12 bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-left transition-colors"
              >
                <div className="font-bold text-[#AFDDFF]">ADMIN</div>
                <div className="text-[9px] text-white/40">admin</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('reviewer')}
                className="p-2 border border-white/12 bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-left transition-colors"
              >
                <div className="font-bold text-[#9FE6C1]">REVIEWER</div>
                <div className="text-[9px] text-white/40">reviewer</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('analyst')}
                className="p-2 border border-white/12 bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-left transition-colors"
              >
                <div className="font-bold text-[#F4C46B]">ANALYST</div>
                <div className="text-[9px] text-white/40">analyst</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('auditor')}
                className="p-2 border border-white/12 bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-left transition-colors"
              >
                <div className="font-bold text-[#D8B4FE]">AUDITOR</div>
                <div className="text-[9px] text-white/40">auditor</div>
              </button>
            </div>
          </div>
        </motion.div>
      </main>

      {/* Footer Disclaimer */}
      <footer className="relative z-10 text-center text-[10px] text-white/30 max-w-6xl mx-auto w-full border-t border-white/10 pt-4 flex justify-between">
        <span>CHARGESHIELD // PRODUCTION HARDENED DECISION PLATFORM</span>
        <span>JWT RBAC PROTOCOL &bull; ENCRYPTED SESSION</span>
      </footer>
    </div>
  );
};
