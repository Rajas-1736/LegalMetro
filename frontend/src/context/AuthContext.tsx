import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { api } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  quickDemoLogin: (role: UserRole) => Promise<void>;
  logout: () => void;
  canManageRules: boolean;
  canScanAndReport: boolean;
}

const DEMO_CREDENTIALS: Record<UserRole, { email: string; pass: string }> = {
  admin: { email: 'admin@visionx.gov.in', pass: 'admin123' },
  inspector: { email: 'inspector@visionx.gov.in', pass: 'inspector123' },
  viewer: { email: 'viewer@visionx.gov.in', pass: 'viewer123' },
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('visionx_token') || localStorage.getItem('legalmetro_token')
  );
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedUser = localStorage.getItem('visionx_user') || localStorage.getItem('legalmetro_user');
      const savedToken = localStorage.getItem('visionx_token') || localStorage.getItem('legalmetro_token');
      if (savedToken && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          localStorage.removeItem('visionx_user');
          localStorage.removeItem('visionx_token');
          localStorage.removeItem('legalmetro_user');
          localStorage.removeItem('legalmetro_token');
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    const data = await api.auth.login(email, pass);
    const authUser: User = {
      id: 1, // populated from token / me
      email: data.email,
      full_name: data.full_name,
      role: data.role as UserRole,
      designation: data.designation,
      badge_number: data.badge_number,
      is_active: true,
    };
    setUser(authUser);
    setToken(data.access_token);
    localStorage.setItem('visionx_token', data.access_token);
    localStorage.setItem('visionx_user', JSON.stringify(authUser));
  };

  const quickDemoLogin = async (role: UserRole) => {
    const creds = DEMO_CREDENTIALS[role];
    await login(creds.email, creds.pass);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('visionx_token');
    localStorage.removeItem('visionx_user');
    localStorage.removeItem('legalmetro_token');
    localStorage.removeItem('legalmetro_user');
  };

  const canManageRules = user?.role === 'admin';
  const canScanAndReport = user?.role === 'admin' || user?.role === 'inspector';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        quickDemoLogin,
        logout,
        canManageRules,
        canScanAndReport,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
