/**
 * Auth Callback Route Handler
 * 
 * NOTE: This route is kept for backwards compatibility.
 * The actual OAuth callback is now handled by the backend at /auth/callback.
 * 
 * The backend:
 * 1. Receives the OAuth callback from Supabase
 * 2. Exchanges the authorization code for a session
 * 3. Sets HttpOnly session cookie
 * 4. Redirects to frontend /dashboard?auth=success
 * 
 * This frontend route just handles post-auth redirect logic.
 * If auth=success, the AuthProvider will fetch /auth/me to hydrate user state.
 */

import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  
  const authStatus = searchParams.get('auth');
  const error = searchParams.get('error');

  // If there's an auth error, redirect to dashboard with error
  if (error) {
    console.error('Auth callback error:', error);
    return NextResponse.redirect(new URL(`/dashboard?error=${encodeURIComponent(error)}`, request.url));
  }

  // If auth was successful, redirect to dashboard
  // The AuthProvider will automatically fetch /auth/me to validate session
  if (authStatus === 'success') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Default: redirect to dashboard (AuthProvider will handle validation)
  return NextResponse.redirect(new URL('/dashboard', request.url));
}
