/**
 * Supabase client - OAuth provider interface only
 * 
 * IMPORTANT: This module is NOT the authentication authority.
 * It's only used for OAuth flow initiation.
 * 
 * Actual authentication is handled by:
 * - Backend: app/routers/auth.py (sets HttpOnly session cookies)
 * - Frontend: lib/auth-context.tsx (calls /auth/me for identity)
 * 
 * This module exists only to provide OAuth provider integration
 * and should not be used for session management or user identity.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Create client only if env vars are available
// This prevents build-time errors when env vars are not set
let supabase: SupabaseClient | null = null;

if (supabaseUrl && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: false, // Don't persist - using backend cookie sessions
      autoRefreshToken: false, // Not used - backend handles refresh
      detectSessionInUrl: false, // Not used - backend handles callback
    },
  });
} else {
  console.warn('Supabase environment variables are not configured.');
}

export { supabase };

/**
 * Sign in with GitHub - initiates OAuth flow via backend
 * 
 * NOTE: This redirects to backend /auth/github, which then handles
 * the OAuth flow with Supabase/GitHub. The frontend should NOT
 * use Supabase directly for authentication.
 * 
 * @deprecated Use authApi.getGitHubAuthUrl() or useAuth().signIn() instead
 * @param redirectTo - URL to redirect after successful authentication (not used)
 */
export async function signInWithGitHub(redirectTo?: string): Promise<void> {
  // This is kept for backwards compatibility but should not be used
  // Instead, use authApi.getGitHubAuthUrl() or redirect to /auth/github
  console.warn('signInWithGitHub is deprecated. Use window.location.href = authApi.getGitHubAuthUrl()');
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  window.location.href = `${API_URL}/auth/github`;
}

/**
 * Sign out - clears session
 * 
 * @deprecated Use useAuth().signOut() instead
 */
export async function signOut(): Promise<void> {
  // This is kept for backwards compatibility but should not be used
  // The backend handles sign out via /auth/signout
  console.warn('signOut is deprecated. Use useAuth().signOut() instead');
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    await fetch(`${API_URL}/auth/signout`, {
      method: 'POST',
      credentials: 'include',
    });
  } catch (error) {
    console.error('Sign out error:', error);
  }
}

/**
 * Get session - NOT FOR AUTHENTICATION
 * 
 * @deprecated Do not use for authentication. Use authApi.me() instead.
 * This may return stale/invalid data.
 */
export async function getSession(): Promise<null> {
  console.warn('getSession is deprecated. Use authApi.me() for authentication.');
  return null;
}

/**
 * Get current user - NOT FOR AUTHENTICATION
 * 
 * @deprecated Do not use for authentication. Use authApi.me() instead.
 * This may return stale/invalid data.
 */
export async function getCurrentUser(): Promise<null> {
  console.warn('getCurrentUser is deprecated. Use authApi.me() for authentication.');
  return null;
}

/**
 * Get access token - NOT FOR AUTHENTICATION
 * 
 * @deprecated Do not use for authentication. Session is managed via HttpOnly cookies.
 */
export async function getAccessToken(): Promise<null> {
  console.warn('getAccessToken is deprecated. Authentication uses HttpOnly cookies.');
  return null;
}

/**
 * Subscribe to auth state changes - NOT SUPPORTED
 * 
 * @deprecated Authentication state is managed by backend. Use useAuth() hook instead.
 */
export function onAuthStateChange(): () => void {
  console.warn('onAuthStateChange is deprecated. Use useAuth() hook for auth state.');
  return () => {};
}
