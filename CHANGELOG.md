# Changelog

All notable changes to the AutoDevOps AI Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-02-20

### Added

#### Repository Governance (Staff-Engineer Level)
- **Trunk-Based Development**: Enforced single-branch workflow with `main` as the only permanent branch
- **Branch Consolidation**: Merged all development branches into `main`, deleted obsolete branches
- **CODEOWNERS**: Code ownership mapping for all repository paths
- **Issue Templates**: Bug report and feature request templates for GitHub Issues
- **PR Template**: Pull request template with trunk-based development compliance checklist
- **Dependabot Configuration**: Automated dependency updates for npm and pip
- **Commitlint**: Conventional Commits enforcement with Husky integration
- **MAINTAINERS.md**: Maintainer responsibilities and contact information
- **CONTRIBUTING.md**: Contribution guidelines with workflow, PR size guidance, and local setup instructions
- **RELEASE.md**: Release process and Semantic Versioning guidelines
- **SECURITY.md**: Security policy and vulnerability disclosure contact
- **docs/adr/ADR-007-repository-structure.md**: Architecture Decision Record for repository governance
- **docs/staff-repo-structure.md**: Staff-engineer repository structure guide
- **docs/engineering_principles.md**: Core engineering principles and standards
- **ops/oncall_playbook.md**: Incident response runbooks for on-call engineers

#### Documentation
- **Founder-level README.md**: Comprehensive technical documentation with system architecture, technology decisions, security model, and operational practices
- **docs/staff-overview.md**: Staff-engineer narrative explaining architectural decisions, trade-offs, and operational considerations
- **docs/architecture.md**: Detailed architecture documentation with Mermaid diagrams for async job lifecycle, deployment topology, and data flows
- **docs/observability.md**: Required metrics, Prometheus endpoints, Grafana dashboards, and SLO/SLI guidance
- GitHub-renderable Mermaid diagrams for system architecture, sequence flows, and state machines
- Technology decision table with rationale and trade-offs
- Clear ownership attribution (Aditya Tiwari, Founder & Lead Engineer)

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