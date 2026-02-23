'use client';

/**
 * Authentication Context - Backend as Single Source of Truth
 * 
 * This module provides authentication state derived from the backend /auth/me endpoint.
 * All identity information comes from the backend, not from the Supabase client.
 * 
 * Authentication flow:
 * 1. On app initialization, call GET /auth/me with credentials: "include"
 * 2. If successful, hydrate user state from response
 * 3. If 401, user is not authenticated
 * 4. signIn() redirects to backend /auth/github which handles OAuth
 * 5. signOut() calls POST /auth/signout to clear session cookie
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi, AuthUser, APIError } from './api';

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider - Wraps the application to provide authentication state
 * 
 * Uses backend /auth/me as single source of truth for user identity.
 * Session is validated via HttpOnly cookies with credentials: "include".
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Fetch user from backend /auth/me endpoint
   * This is the single source of truth for authentication state
   */
  const fetchUser = async () => {
    try {
      const userData = await authApi.me();
      setUser(userData);
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        // Not authenticated - clear user state
        setUser(null);
      } else {
        // Network error or other issue - keep existing state but stop loading
        console.error('Failed to fetch user:', error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Initial session validation on mount
  useEffect(() => {
    fetchUser();
  }, []);

  /**
   * Sign in - redirects to backend OAuth flow
   * The backend /auth/github endpoint handles the OAuth redirect to GitHub
   */
  const signIn = async () => {
    // Redirect to backend OAuth endpoint
    // This will redirect to GitHub, then back to backend callback,
    // which sets the session cookie and redirects to frontend
    const authUrl = authApi.getGitHubAuthUrl();
    window.location.href = authUrl;
  };

  /**
   * Sign out - clears session cookie via backend
   */
  const signOut = async () => {
    try {
      await authApi.signout();
    } catch (error) {
      console.error('Sign out error:', error);
    } finally {
      setUser(null);
    }
  };

  /**
   * Refresh user - re-validate session with backend
   * Useful after session changes or to force re-validation
   */
  const refreshUser = async () => {
    setIsLoading(true);
    await fetchUser();
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    signIn,
    signOut,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 * @throws Error if used outside AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
