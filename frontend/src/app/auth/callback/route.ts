/**
 * Auth Callback Route Handler
 * Handles OAuth callback from Supabase after GitHub authentication.
 * This route processes the authorization code and exchanges it for a session.
 */

import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  
  const code = searchParams.get('code');
  const next = searchParams.get('next') ?? '/dashboard';

  if (code) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
      console.error('Missing Supabase environment variables');
      return NextResponse.redirect(new URL('/dashboard?error=configuration', request.url));
    }

    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    try {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code);

      if (error) {
        console.error('Auth callback error:', error.message);
        return NextResponse.redirect(new URL('/dashboard?error=' + encodeURIComponent(error.message), request.url));
      }

      console.log('Session established successfully:', data.user?.id);
      
      // Redirect to dashboard after successful authentication
      return NextResponse.redirect(new URL(next, request.url));
    } catch (err) {
      console.error('Unexpected auth callback error:', err);
      return NextResponse.redirect(new URL('/dashboard?error=unknown', request.url));
    }
  }

  // If no code, redirect to dashboard (user may already be logged in or auth was cancelled)
  return NextResponse.redirect(new URL(next, request.url));
}
</parameter>
<task_progress>
- [x] Analyze authentication issue
- [x] Fix API client with credentials: 'include'
- [x] Add NEXT_PUBLIC_FRONTEND_URL environment variable
- [x] Create auth callback route
- [ ] Update Supabase client configuration
- [ ] Create vercel.json for CORS headers
- [ ] Commit and push changes
- [ ] Verify deployment and authentication flow
</task_progress>
</invoke>
</minimax:tool_call>