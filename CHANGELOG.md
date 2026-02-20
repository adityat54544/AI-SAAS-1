# Changelog

All notable changes to the AutoDevOps AI Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-02-20

### Added

#### Infrastructure & Deployment
- Railway service separation with three distinct services (API, worker, cron)
- Service-specific Dockerfiles with security hardening
- Non-root user execution in all containers
- Health checks and resource constraints
- Railway deployment configuration with auto-scaling

#### Security Hardening
- Webhook signature verification using HMAC-SHA256
- Rate limiting with Redis-backed slowapi
- Structured JSON logging with correlation IDs (request_id, job_id, user_id)
- Secret rotation scripts for Supabase and Gemini API keys
- Git history secret removal script with dry-run mode
- Pre-commit hooks for secret detection and code quality

#### Cost Controls & AI Usage
- Per-user and per-repository AI usage quotas
- Token estimation utility for cost prediction
- Intelligent model routing (Gemini 1.5 Flash vs Gemini 2.5 Pro)
- AI usage tracking and cost monitoring
- Billing alerts configuration

#### Resilience Patterns
- Circuit breaker for AI API calls with configurable thresholds
- Exponential backoff with jitter for retries
- Timeout handling with fallback responses
- Graceful degradation when AI services unavailable

#### Observability
- Prometheus metrics export (/metrics endpoint)
- Grafana dashboard template for monitoring
- Sentry integration for error reporting
- Alert configuration for billing and performance

#### Backups & Disaster Recovery
- Automated PostgreSQL backup script with S3 upload
- Backup retention configuration
- Restore procedures documentation

#### CI/CD
- Comprehensive CI pipeline with security scanning
- Gitleaks and detect-secrets integration
- Bandit SAST scanning for Python
- Infrastructure lint checks
- Docker image build and push workflow
- Railway deployment automation

#### Documentation
- Operations runbook with incident procedures
- Verification procedures for deployments
- Railway deployment guide
- Branch protection configuration guide
- Security report with SOC 2 readiness assessment
- Auto-scaler documentation

#### Testing
- AI resilience unit tests (circuit breaker, retry logic)
- End-to-end job flow tests
- Webhook verification tests
- Token encryption round-trip tests

### Changed
- Improved error handling with structured responses
- Enhanced logging with sensitive data redaction
- Updated environment variable configuration

### Security
- Added CORS policy whitelisting
- Implemented rate limiting on all endpoints
- Added webhook verification for GitHub integration
- Enhanced secret management practices

## [0.1.0] - Previous Release

### Added
- Initial FastAPI backend with Supabase integration
- GitHub OAuth authentication
- Basic AI analysis functionality
- Frontend dashboard with Next.js
- BullMQ worker for background jobs