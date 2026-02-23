#!/usr/bin/env ts-node
/**
 * Startup Validation Script
 * 
 * Validates required environment variables and connectivity before server starts.
 * This prevents broken frontend launches in production.
 * 
 * Usage: ts-node scripts/startup-validation.ts
 */

const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
];

interface ValidationResult {
  success: boolean;
  errors: string[];
  warnings: string[];
}

function log(level: 'INFO' | 'WARN' | 'ERROR', message: string, data?: Record<string, unknown>): void {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    level,
    service: 'startup-validation',
    message,
    ...data,
  };
  console.log(JSON.stringify(logEntry));
}

function validateEnvironmentVariables(): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  log('INFO', 'Validating environment variables...');

  for (const varName of requiredEnvVars) {
    const value = process.env[varName];
    
    if (!value) {
      errors.push(`Missing required environment variable: ${varName}`);
      log('ERROR', `Missing env var: ${varName}`);
    } else if (value === 'undefined' || value === 'null') {
      errors.push(`Invalid value for ${varName}: got "${value}"`);
      log('ERROR', `Invalid env var value: ${varName}`, { value });
    } else if (varName === 'NEXT_PUBLIC_API_URL') {
      // Validate URL format
      try {
        new URL(value);
        log('INFO', `Validated: ${varName}`, { url: value });
      } catch {
        errors.push(`Invalid URL format for ${varName}: ${value}`);
        log('ERROR', `Invalid URL: ${varName}`, { value });
      }
    } else if (varName === 'NEXT_PUBLIC_SUPABASE_URL') {
      // Validate Supabase URL format
      try {
        const url = new URL(value);
        if (!url.hostname.includes('supabase.co')) {
          warnings.push(`Supabase URL doesn't appear to be from supabase.co: ${value}`);
        }
        log('INFO', `Validated: ${varName}`, { url: value });
      } catch {
        errors.push(`Invalid URL format for ${varName}: ${value}`);
      }
    } else {
      log('INFO', `Validated: ${varName}`, { length: value.length });
    }
  }

  // Check for localhost in production
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (apiUrl && apiUrl.includes('localhost')) {
    warnings.push('NEXT_PUBLIC_API_URL contains localhost - this may cause issues in production');
    log('WARN', 'Production check: localhost detected in API URL', { apiUrl });
  }

  return {
    success: errors.length === 0,
    errors,
    warnings,
  };
}

function validatePort(): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  log('INFO', 'Validating PORT configuration...');

  const port = process.env.PORT;
  
  if (!port) {
    // PORT is optional - Railway sets it dynamically
    warnings.push('PORT not set - will use default 3000');
    log('WARN', 'PORT not set, using default');
  } else {
    const portNum = parseInt(port, 10);
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      errors.push(`Invalid PORT value: ${port} (must be 1-65535)`);
      log('ERROR', 'Invalid PORT', { port });
    } else {
      log('INFO', 'PORT validated', { port: portNum });
    }
  }

  return { success: errors.length === 0, errors, warnings };
}

async function validateApiConnectivity(): Promise<ValidationResult> {
  const errors: string[] = [];
  const warnings: string[] = [];

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    warnings.push('Cannot validate API connectivity - NEXT_PUBLIC_API_URL not set');
    return { success: true, errors, warnings };
  }

  log('INFO', 'Validating API connectivity...', { apiUrl });

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(`${apiUrl}/health`, {
      method: 'HEAD',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok || response.status === 405) {
      // 405 Method Not Allowed is OK - means server is running
      log('INFO', 'API is reachable', { status: response.status, apiUrl });
    } else {
      warnings.push(`API returned status ${response.status} - may be degraded`);
      log('WARN', 'API returned non-OK status', { status: response.status, apiUrl });
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    if (message.includes('abort')) {
      warnings.push(`API connectivity check timed out after 5s - backend may be slow`);
      log('WARN', 'API connectivity timeout', { apiUrl });
    } else {
      warnings.push(`Cannot reach API at ${apiUrl}: ${message}`);
      log('WARN', 'API connectivity failed', { apiUrl, error: message });
    }
  }

  return { success: true, errors, warnings }; // Don't block startup for connectivity issues
}

async function main(): Promise<void> {
  const startTime = Date.now();
  
  log('INFO', '=== STARTUP VALIDATION BEGINNING ===');
  log('INFO', 'Node version', { version: process.version });
  log('INFO', 'Environment', { nodeEnv: process.env.NODE_ENV });

  const results: ValidationResult[] = [];

  // Run all validations
  results.push(validateEnvironmentVariables());
  results.push(validatePort());
  results.push(await validateApiConnectivity());

  // Aggregate results
  const allErrors = results.flatMap(r => r.errors);
  const allWarnings = results.flatMap(r => r.warnings);

  const duration = Date.now() - startTime;

  // Log summary
  log('INFO', 'Validation summary', {
    duration_ms: duration,
    errors_count: allErrors.length,
    warnings_count: allWarnings.length,
  });

  if (allWarnings.length > 0) {
    log('WARN', 'Validation warnings:', { warnings: allWarnings });
  }

  if (allErrors.length > 0) {
    log('ERROR', 'Validation FAILED - blocking startup', { errors: allErrors });
    console.error('\n❌ STARTUP VALIDATION FAILED\n');
    console.error('Errors found:');
    allErrors.forEach(err => console.error(`  - ${err}`));
    console.error('\n');
    process.exit(1); // Fail intentionally - prevent broken deployment
  }

  log('INFO', '=== STARTUP VALIDATION PASSED ===', { duration_ms: duration });
  console.log('\n✅ Startup validation passed\n');
}

// Run if executed directly
main().catch((error) => {
  const message = error instanceof Error ? error.message : 'Unknown error';
  log('ERROR', 'Validation script crashed', { error: message });
  console.error(`\n❌ Validation script crashed: ${message}\n`);
  process.exit(1);
});
