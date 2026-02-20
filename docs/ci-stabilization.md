# CI Pipeline Stabilization Guide

**Date:** 2026-02-21  
**Status:** ✅ Complete

## Overview

This document describes the changes made to stabilize the GitHub Actions CI pipeline and local development environment for the AutoDevOps AI Platform.

## Changes Summary

### 1. Environment Configuration (`app/config.py`)

**Problem:** Required credentials caused import failures in CI when secrets were unavailable.

**Solution:**
- Added `_is_test_environment()` function to detect CI/test environments
- Implemented safe fallback values for all required credentials when `ENVIRONMENT=test` or `CI=true`
- Added helper methods to check if real credentials are configured:
  - `has_supabase_config()` - Check if real Supabase credentials exist
  - `has_github_config()` - Check if real GitHub OAuth credentials exist
  - `has_gemini_config()` - Check if real Gemini API key exists
  - `has_redis_config()` - Check if Redis URL is configured

**Test Fallback Values:**
```python
SUPABASE_URL = "https://test-project.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "test-service-role-key"
GITHUB_CLIENT_ID = "test-github-client-id"
GEMINI_API_KEY = "test-gemini-api-key"
JWT_SECRET = "test-jwt-secret-for-ci-testing-only"
ENCRYPTION_KEY = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcy1sb25n"
```

### 2. Supabase Client (`app/supabase_client.py`)

**Problem:** Supabase client raised `ValueError` on import when credentials were missing.

**Solution:**
- Created `_create_mock_supabase()` function to return a mock client in test environments
- Mock client responds with standard test data for common operations
- Added `is_real_supabase()` function to check if using real connection

### 3. Gemini Provider (`app/ai/gemini_provider.py`)

**Problem:** Gemini provider failed to initialize without a valid API key.

**Solution:**
- Added `_is_mock` flag to track mock mode
- Created `_generate_mock_response()` method for test responses
- Mock responses return valid JSON for analysis and CI generation requests
- Test API keys (starting with "test-") automatically enable mock mode

### 4. CI Workflow (`.github/workflows/ci.yml`)

**Changes:**
- Added concurrency control to cancel in-progress runs for the same branch
- Fixed `docker compose` validation command (using `docker compose` instead of `docker-compose`)
- All secrets use fallback syntax: `${{ secrets.X || 'fallback' }}`

### 5. Test Configuration (`tests/conftest.py`)

**Changes:**
- Set `ENVIRONMENT=test` and `CI=true` before importing app modules
- Added additional pytest markers:
  - `@pytest.mark.supabase` - Requires Supabase connection
  - `@pytest.mark.github` - Requires GitHub API
  - `@pytest.mark.gemini` - Requires Gemini API

## Environment Variables

### Required for Production

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `REDIS_URL` | Redis connection URL | Yes |

### Optional for Development

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `JWT_SECRET` | JWT signing secret | Auto-generated |
| `ENCRYPTION_KEY` | AES-256 encryption key | None |
| `GITHUB_WEBHOOK_SECRET` | Webhook verification secret | None |

### Redis Configuration

| Variable | Description |
|----------|-------------|
| `REDIS_URL` | Primary Redis URL (Upstash or local) |
| `SUPABASE_REDIS_URL` | Supabase-managed Redis (takes precedence) |
| `SUPABASE_REDIS_PASSWORD` | Password for Supabase Redis |

## GitHub Actions Secrets Setup

Navigate to: **Settings → Secrets and variables → Actions → New repository secret**

### Minimum Required Secrets

```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GEMINI_API_KEY
REDIS_URL (or use CI-provided Redis service)
```

### Optional Secrets

```
SUPABASE_ANON_KEY
GITHUB_WEBHOOK_SECRET
JWT_SECRET
ENCRYPTION_KEY
```

## Local Development Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your credentials in `.env`

3. Start Redis (via Docker):
   ```bash
   docker compose up -d redis
   ```

4. Run tests:
   ```bash
   ENVIRONMENT=test pytest tests/ -v
   ```

## CI Behavior

### Without Secrets Configured

- Tests run with mock services
- All external API calls return test data
- CI passes with safe fallbacks
- Logs show: "Using mock client for test environment"

### With Secrets Configured

- Tests run against real services
- External API calls use real credentials
- Integration tests execute fully

## Testing

### Run Unit Tests (No External Dependencies)
```bash
ENVIRONMENT=test pytest tests/ -v -m "not integration"
```

### Run All Tests
```bash
ENVIRONMENT=test pytest tests/ -v
```

### Run with Coverage
```bash
ENVIRONMENT=test pytest tests/ -v --cov=app --cov-report=xml
```

## Deployment Readiness

### Railway Deployment

1. Set environment variables in Railway dashboard
2. Deploy using the Railway CLI or GitHub integration
3. Health checks available at `/health` and `/ready`

### Vercel Deployment (Frontend)

1. Set `NEXT_PUBLIC_API_URL` to your backend URL
2. Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Deploy via Vercel CLI or GitHub integration

## Troubleshooting

### Tests Failing with Import Errors

- Ensure `ENVIRONMENT=test` is set
- Check all dependencies are installed: `pip install -r requirements.txt`

### Redis Connection Issues

- Verify Redis is running: `redis-cli ping`
- Check `REDIS_URL` environment variable
- CI uses built-in Redis service container

### Supabase Connection Issues

- Verify credentials in `.env`
- Check Supabase project is running
- Test with `python test_supabase.py`

## Security Notes

- ✅ No secrets committed to repository
- ✅ `.env` is gitignored
- ✅ Test credentials are clearly marked as test values
- ✅ Real credentials only loaded in production
- ✅ All secrets accessed via environment variables