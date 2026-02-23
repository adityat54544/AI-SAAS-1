import { NextResponse } from 'next/server';

/**
 * Health check endpoint for Railway deployment
 * 
 * Returns 200 OK when:
 * - Server is running
 * - Can parse environment variables
 * 
 * Used by Railway healthcheck and deployment probes
 */
export async function GET() {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'frontend',
    checks: {
      env_vars: checkEnvVars(),
    },
  };

  // Check for critical env vars
  const envOk = health.checks.env_vars;
  
  if (!envOk) {
    return NextResponse.json(
      { status: 'unhealthy', error: 'Missing required environment variables' },
      { status: 503 }
    );
  }

  return NextResponse.json(health, { status: 200 });
}

function checkEnvVars(): boolean {
  const required = [
    'NEXT_PUBLIC_API_URL',
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  ];

  return required.every(v => !!process.env[v]);
}

// HEAD request for Railway TCP healthcheck
export async function HEAD() {
  return new NextResponse(null, { status: 200 });
}
