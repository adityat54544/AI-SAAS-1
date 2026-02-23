/**
 * Supabase client configuration for frontend authentication.
 * Handles OAuth authentication and session management.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import type { Session, User } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Create client only if env vars are available
// This prevents build-time errors when env vars are not set
let supabase: SupabaseClient | null = null;

if (supabaseUrl && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
} else {
  console.warn('Supabase environment variables are not configured. Authentication will not work.');
}

export { supabase };

/**
 * Sign in with GitHub OAuth provider
 * @param redirectTo - URL to redirect after successful authentication
 */
export async function signInWithGitHub(redirectTo?: string) {
  if (!supabase) {
    throw new Error('Supabase client not initialized');
  }

  // Use explicit callback URL for proper OAuth flow
  const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';
  const callbackUrl = `${frontendUrl}/auth/callback`;
  
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'github',
    options: {
      redirectTo: redirectTo || callbackUrl,
      scopes: 'repo user:email',
    },
  });

  if (error) {
    console.error('GitHub sign-in error:', error);
    throw error;
  }

  return data;
}

/**
 * Sign out the current user
 */
export async function signOut() {
  if (!supabase) {
    throw new Error('Supabase client not initialized');
  }
  const { error } = await supabase.auth.signOut();
  if (error) {
    console.error('Sign-out error:', error);
    throw error;
  }
}

/**
 * Get the current session
 * @returns Session object or null if not authenticated
 */
export async function getSession(): Promise<Session | null> {
  if (!supabase) {
    return null;
  }
  const { data: { session }, error } = await supabase.auth.getSession();
  if (error) {
    console.error('Get session error:', error);
    return null;
  }
  return session;
}

/**
 * Get the current user
 * @returns User object or null if not authenticated
 */
export async function getCurrentUser(): Promise<User | null> {
  if (!supabase) {
    return null;
  }
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error) {
    console.error('Get user error:', error);
    return null;
  }
  return user;
}

/**
 * Get the current access token
 * @returns Access token string or null if not authenticated
 */
export async function getAccessToken(): Promise<string | null> {
  const session = await getSession();
  return session?.access_token || null;
}

/**
 * Subscribe to auth state changes
 * @param callback - Callback function to handle auth state changes
 * @returns Unsubscribe function
 */
export function onAuthStateChange(
  callback: (event: string, session: Session | null) => void
) {
  if (!supabase) {
    return () => {};
  }
  const { data: { subscription } } = supabase.auth.onAuthStateChange(callback);
  return () => subscription.unsubscribe();
}
