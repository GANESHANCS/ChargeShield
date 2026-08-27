import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { isAuthenticated, hasRole, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !hasRole(allowedRoles)) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center font-mono select-none">
        <div className="border border-[#E68A8A]/30 bg-[#E68A8A]/5 p-8 max-w-lg w-full backdrop-blur-md">
          <div className="text-[10px] text-[#E68A8A] font-bold tracking-widest uppercase mb-2">
            [ 403 // FORBIDDEN ACCESS ]
          </div>
          <h2 className="text-2xl font-display font-light text-white mb-4">
            ACCESS DENIED
          </h2>
          <p className="text-xs text-white/60 mb-6 leading-relaxed">
            Your user role <span className="text-[#AFDDFF] font-bold">[{user?.role}]</span> does not possess the operational permissions required for this module ({allowedRoles.join(', ')} required).
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-5 py-2 bg-white/10 hover:bg-white/20 text-white text-xs border border-white/20 tracking-wider uppercase transition-colors"
          >
            [ RETURN TO PREVIOUS PAGE ]
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
