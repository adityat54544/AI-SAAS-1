# CI Redis Issue Report

**Date:** 2026-02-20  
**Branch:** fix/ci-redis-supabase  
**Author:** DevOps CI Engineer

## Executive Summary

Analysis of the CI pipeline identified potential issues related to Redis service configuration and missing environment variable handling. This report documents the findings and the fixes implemented.

## Redis Usage Analysis

### Components Using Redis

| Component | File | Purpose |
|-----------|------|---------|
| Job Service | `app/services/job_service.py` | Queue management, job processing |
| Rate Limiting | `app/middleware/rate_limit.py` | Request rate limiting |
| AI Guard | `app/ai/guard.py` | Distributed quota tracking |
| Health Checks | `app/main.py` | Service health verification |
| Workers | `workers/src/index.ts` | BullMQ queue processing |

### Current CI Configuration

The `.github/workflows/ci.yml` configures Redis service containers for:
- `backend-test` job
- `workers-test` job
- `integration-test` job

Each job uses:
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
```

## Identified Issues

### Issue 1: Missing Fallback Logic
**Severity:** Medium  
**Description:** CI jobs lack conditional logic to handle cases where the Redis service container fails to start or is unavailable. Jobs may fail without clear error messages.

**Missing Environment Variables:**
- `REDIS_URL` - Not always passed from secrets
- No fallback to CI-provided Redis service

### Issue 2: No Supabase Redis Support
**Severity:** Medium  
**Description:** The application does not support Supabase-provided Redis as an alternative to a standalone Redis instance. Users cannot leverage Supabase's managed Redis service.

**Missing Environment Variables:**
- `SUPABASE_REDIS_URL` - Connection string for Supabase Redis
- `SUPABASE_REDIS_PASSWORD` - Password for Supabase Redis

### Issue 3: Test Resilience
**Severity:** Low  
**Description:** Test fixtures lack proper mocking for Redis-dependent tests, potentially causing test failures when Redis is unavailable.

### Issue 4: No Redis Source Detection
**Severity:** Low  
**Description:** CI jobs do not log whether they're using external Redis secrets or the CI-provided Redis service, making debugging difficult.

## Fix Implementation

### Commit 1: CI Redis Service Fallback
- Enhanced CI workflow with proper fallback logic
- Added Redis environment detection step
- Ensured CI-provided Redis is used when external secrets unavailable

### Commit 2: Supabase Redis Support
- Added `SUPABASE_REDIS_URL` and `SUPABASE_REDIS_PASSWORD` support to `app/config.py`
- Updated `.env.example` with new environment variables

### Commit 3: Redis Setup Documentation
- Created `docs/redis-setup.md` with Upstash and Supabase Redis instructions
- Documented GitHub Actions secret configuration

### Commit 4: Test Resilience
- Enhanced test fixtures with Redis mock support
- Added pytest markers for integration tests requiring Redis
- Made unit tests independent of Redis availability

### Commit 5: CI Secrets Detection
- Added environment detection step at start of affected CI jobs
- Logs Redis source without exposing secret values

## Manual Steps Required

### For Supabase Redis Users:
1. Navigate to Supabase Dashboard → Project Settings → Database
2. Find Redis connection string under "Connection Pooling" or "Redis"
3. Copy the connection URL and password
4. Add to GitHub Actions Secrets:
   - `SUPABASE_REDIS_URL` - Full Redis connection URL
   - `SUPABASE_REDIS_PASSWORD` - Redis password

### For Upstash Redis Users:
1. Create free account at https://upstash.com
2. Create a new Redis database
3. Copy the Redis URL from dashboard
4. Add to GitHub Actions Secrets:
   - `REDIS_URL` - Upstash Redis URL (format: `redis://default:PASSWORD@HOST:6379`)

## Validation

After merging this PR:
1. Verify CI jobs pass with CI-provided Redis
2. Configure external Redis (Supabase or Upstash) in repository secrets
3. Re-run CI jobs to verify external Redis integration
4. Check CI logs for Redis source detection message

## Security Notes

- No secret values are committed to the repository
- All Redis credentials are handled via environment variables
- GitHub Actions secrets should be configured for production deployments
- CI-provided Redis is only used for testing, not production