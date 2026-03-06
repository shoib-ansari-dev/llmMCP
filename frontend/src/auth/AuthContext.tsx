/**
 * Authentication Context
 * Provides authentication state and methods to the app.
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { AuthState, LoginCredentials, RegisterData } from './types';
import {
  checkDevMode,
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser,
  getAccessToken,
  setupAuthInterceptor,
} from './api';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    isDevMode: false,
  });

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Setup interceptor for token refresh
        setupAuthInterceptor();

        // Check if dev mode is enabled
        const devMode = await checkDevMode();

        if (devMode) {
          // In dev mode, get the dev user
          const user = await getCurrentUser();
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
            isDevMode: true,
          });
          return;
        }

        // Check if user has a valid token
        const token = getAccessToken();
        if (token) {
          try {
            const user = await getCurrentUser();
            setState({
              user,
              isAuthenticated: true,
              isLoading: false,
              isDevMode: false,
            });
            return;
          } catch {
            // Token invalid, clear state
          }
        }

        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isDevMode: false,
        });
      } catch (error) {
        console.error('Auth initialization error:', error);
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isDevMode: false,
        });
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    try {
      await apiLogin(credentials);
      const user = await getCurrentUser();
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        isDevMode: false,
      });
    } catch (error) {
      setState((prev) => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    try {
      await apiRegister(data);
      const user = await getCurrentUser();
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        isDevMode: false,
      });
    } catch (error) {
      setState((prev) => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isDevMode: state.isDevMode,
    });
  }, [state.isDevMode]);

  const refreshUser = useCallback(async () => {
    try {
      const user = await getCurrentUser();
      setState((prev) => ({ ...prev, user }));
    } catch {
      // Ignore errors
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

