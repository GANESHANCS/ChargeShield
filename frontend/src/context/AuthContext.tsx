import React, { createContext, useContext, useState, useEffect } from 'react';

export interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  role: string; // ADMIN, ANALYST, REVIEWER, AUDITOR
  full_name: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (allowedRoles: string[]) => boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'chargeshield_auth_token';
const USER_KEY = 'chargeshield_auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem(USER_KEY);
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  const login = async (username: string, password: string) => {
    const apiBaseUrl = (import.meta as any).env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const message = errData.detail || errData.error || 'Authentication failed. Invalid credentials.';
        throw new Error(typeof message === 'string' ? message : 'Authentication failed.');
      }

      const data = await res.json();
      setToken(data.access_token);
      setUser(data.user);
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Authentication server timeout. Please check backend connection.');
      }
      if (err.message === 'Failed to fetch' || err.message?.includes('fetch')) {
        throw new Error('Unable to connect to authentication server. Please check connection.');
      }
      throw err;
    }
  };

  const logout = () => {
    if (token) {
      const apiBaseUrl = (import.meta as any).env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      fetch(`${apiBaseUrl}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }).catch(() => {});
    }
    setToken(null);
    setUser(null);
  };

  const hasRole = (allowedRoles: string[]): boolean => {
    if (!user) return false;
    if (user.role.toUpperCase() === 'ADMIN') return true;
    return allowedRoles.map(r => r.toUpperCase()).includes(user.role.toUpperCase());
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        hasRole,
        isAuthenticated: !!token && !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
