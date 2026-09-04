import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { NavigationRail } from './components/NavigationRail';
import { GridBackground } from './components/visual/GridBackground';
import { PageTransition } from './components/visual/PageTransition';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { IntroPage } from './pages/IntroPage';
import { DashboardPage } from './pages/DashboardPage';
import { QueuePage } from './pages/QueuePage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { ModelPage } from './pages/ModelPage';
import { AuditPage } from './pages/AuditPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SimulationPage } from './pages/SimulationPage';
import { api } from './services/api';

function AppContent() {
  const location = useLocation();
  const [, setBackendOnline] = useState<boolean>(true);

  useEffect(() => {
    window.onerror = (message, _source, _lineno, _colno, error) => {
      console.error('CRITICAL_DOM_ERROR:', message, error?.stack || error);
    };
    window.onunhandledrejection = (event) => {
      console.error('UNHANDLED_REJECTION:', event.reason?.stack || event.reason);
    };

    async function checkBackend() {
      try {
        await api.getHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    }
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  const isLandingOrLogin = location.pathname === '/' || location.pathname === '/login' || location.pathname === '/intro';

  return (
    <div className="min-h-screen w-full bg-[#05070D] text-white font-sans antialiased relative selection:bg-[#AFDDFF] selection:text-black flex flex-col">
      {/* Background Grid */}
      <GridBackground />

      {/* Top Sticky LŪMEN Navigation Rail (hidden on /login and /intro) */}
      {location.pathname !== '/login' && location.pathname !== '/intro' && <NavigationRail />}

      {/* Main Content Area */}
      <main className="flex-1 w-full relative z-10">
        <PageTransition key={location.pathname}>
          <Routes location={location}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/intro" element={<IntroPage />} />
            <Route path="/login" element={<LoginPage />} />
            
            {/* Operational Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/queue"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST', 'REVIEWER']}>
                  <QueuePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/cases"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST', 'REVIEWER']}>
                  <CaseDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/cases/:disputeId"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST', 'REVIEWER']}>
                  <CaseDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/model"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST']}>
                  <ModelPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST', 'AUDITOR']}>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST', 'REVIEWER', 'AUDITOR']}>
                  <AuditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/simulation"
              element={
                <ProtectedRoute allowedRoles={['ADMIN', 'ANALYST', 'REVIEWER', 'AUDITOR']}>
                  <SimulationPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </PageTransition>
      </main>

      {!isLandingOrLogin && (
        <footer className="border-t border-white/12 py-4 px-[20px] md:px-[35px] text-center text-[10px] text-white/40 font-mono flex flex-col sm:flex-row items-center justify-between gap-2 bg-black/90 backdrop-blur-md select-none z-20">
          <span>CHARGESHIELD // AI RISK INTELLIGENCE PLATFORM</span>
          <span>HUMAN-IN-THE-LOOP AUTHORIZATION BOUNDARY &bull; NO AUTONOMOUS REVERSALS</span>
        </footer>
      )}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}
