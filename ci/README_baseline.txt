# CI Baseline Report
# Date: 2026-02-20
# Branch: fix/ci-redis-supabase

## Summary

This baseline report documents the state of the CI pipeline after implementing
Redis fallback support and Supabase Redis integration.

## Changes Implemented

### 1. CI Workflow Updates (.github/workflows/ci.yml)

- Added Redis service fallback with persistence options:
  * --save 60 1
  * --appendonly yes

- Added Redis environment detection step to all Redis-dependent jobs:
  * backend-test
  * workers-test
  * integration-test

- Environment variables now support fallback:
  * REDIS_URL: ${{ secrets.REDIS_URL || 'redis://localhost:6379/0' }}
  * SUPABASE_REDIS_URL: ${{ secrets.SUPABASE_REDIS_URL }}
  * SUPABASE_REDIS_PASSWORD: ${{ secrets.SUPABASE_REDIS_PASSWORD }}

### 2. Configuration Updates (app/config.py)

- Added new environment variables:
  * supabase_redis_url: Optional[str] = None
  * supabase_redis_password: Optional[str] = None

- Added helper properties:
  * effective_redis_url: Returns the correct Redis URL based on priority
  * effective_redis_password: Returns the correct Redis password

### 3. Environment Example (.env.example)

- Documented new Supabase Redis configuration options
- Added clear comments explaining priority order

### 4. Test Infrastructure (tests/conftest.py, pytest.ini)

- Added pytest markers:
  * @pytest.mark.integration - For tests requiring Redis
  * @pytest.mark.unit - For isolated tests
  * @pytest.mark.redis - For Redis-specific tests

- Added mock fixtures:
  * mock_redis: Synchronous Redis mock
  * mock_redis_async: Async Redis mock
  * redis_url: Configurable Redis URL fixture

- Integration tests are automatically skipped when Redis is unavailable

### 5. Documentation (docs/redis-setup.md)

- Complete guide for Redis configuration
- Upstash free tier setup instructions
- Supabase Redis setup instructions
- GitHub Actions secrets configuration guide

## Test Categories

### Unit Tests (always run)
- tests/test_health.py
- tests/test_basic.py
- tests/test_ai_resilience.py

### Integration Tests (require Redis or skipped)
- tests/integration/ (if exists)
- tests/e2e_job_flow.py (partial mocking)

## Required GitHub Actions Secrets

### Required for Production
| Secret Name | Description |
|-------------|-------------|
| SUPABASE_URL | Supabase project URL |
| SUPABASE_SERVICE_ROLE_KEY | Supabase service role key |
| GITHUB_CLIENT_ID | GitHub OAuth client ID |
| GITHUB_CLIENT_SECRET | GitHub OAuth client secret |
| GEMINI_API_KEY | Google Gemini API key |

### Redis Configuration (at least one required for production)
| Secret Name | Description |
|-------------|-------------|
| REDIS_URL | Redis connection URL (Upstash or self-hosted) |
| REDIS_PASSWORD | Redis password (optional) |
| SUPABASE_REDIS_URL | Supabase Redis URL |
| SUPABASE_REDIS_PASSWORD | Supabase Redis password |

## CI Job Flow

1. security-scan (parallel)
   - detect-secrets
   - gitleaks
   - bandit

2. backend-test (needs: security-scan)
   - Uses Redis service container
   - Runs unit tests
   - Reports coverage

3. frontend-test (needs: security-scan)
   - npm ci
   - lint
   - build

4. workers-test (needs: security-scan)
   - Uses Redis service container
   - npm ci
   - lint
   - build
   - test

5. integration-test (needs: backend-test, frontend-test, workers-test)
   - Uses Redis service container
   - Runs integration tests
   - Runs E2E tests

6. build (needs: backend-test, frontend-test, workers-test)
   - Builds Docker images
   - Pushes to ghcr.io

7. deploy (needs: build)
   - Deploys to Railway

## Expected CI Behavior

### Without External Redis Secrets
- CI uses Redis service container (redis:7-alpine)
- All tests run against localhost:6379
- Integration tests pass with CI-provided Redis

### With External Redis Secrets
- CI detects external Redis configuration
- Logs "Using External REDIS_URL secret" or similar
- Tests run against external Redis instance

## Verification Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run linting
ruff check app/

# Run type checking
mypy app/ --ignore-missing-imports

# Run unit tests only
pytest tests/ -v -m "not integration"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Notes

- CI will always provide a Redis service container as fallback
- External Redis is recommended for production deployments
- Unit tests should pass without any external dependencies
- Integration tests are skipped if Redis is unavailable