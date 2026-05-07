import { createContext, useContext, type ReactNode } from 'react';
import { useStore } from '../store';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  role: 'admin' | 'staff' | null;
  login: (username: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const store = useStore();

  const login = async (username: string) => {
    const role = username.toLowerCase().includes('admin') ? 'admin' : 'staff';
    store.setUser({ id: 1, username, role }, role);
  };

  const logout = () => {
    store.setUser(null, null);
  };

  const value: AuthContextType = {
    user: store.user,
    role: store.role,
    login,
    logout,
    isAdmin: store.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
