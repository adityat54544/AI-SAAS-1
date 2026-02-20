# ADR-007: Repository Structure & Governance

## Status

**Accepted** - 2026-02-20

## Context

The AutoDevOps AI Platform has evolved from an initial prototype to a production-ready multi-tenant SaaS application. As the platform matures, we need to establish a clear repository structure and governance model that:

1. Supports single-owner development while enabling future team growth
2. Enforces code quality and security standards
3. Provides clear documentation for onboarding and operations
4. Follows industry best practices for trunk-based development
5. Enables compliance with security and operational standards

The repository previously lacked:
- Formal governance documentation
- Clear ownership definitions
- Standardized contribution workflows
- Release process documentation
- Staff-engineer level structural guidance

## Decision

### 1. Single-Owner CODEOWNERS Model

We adopt a single-owner CODEOWNERS configuration mapping all paths to `@adityat54544`.

**Rationale:**
- Reflects current team structure (single developer)
- Establishes clear architectural ownership
- Enables automatic PR review requests
- Signals founder-style repository ownership
- Simplifies governance enforcement

### 2. Trunk-Based Development Workflow

We enforce a strict trunk-based development model with `main` as the only permanent branch.

**Rules:**
- All changes via pull request
- Feature branches exist for maximum 3 days
- No long-lived branches (`develop`, `staging`, `release/*`)
- `main` is always deployable
- Squash merge by default

**Branch Protection (GitHub Settings):**
- Require pull request before merging (1 approval minimum)
- Require status checks to pass (CI workflow)
- Require linear history
- Block force pushes
- Block branch deletion
- Automatically delete head branches
- Require conversation resolution before merge

### 3. Semantic Commit Enforcement

We enforce Conventional Commits specification via:
- commitlint workflow in CI
- PR title validation
- Pre-commit hooks (optional, recommended)

**Version Bump Rules:**
| Commit Type | Version Bump |
|-------------|--------------|
| `feat:` | MINOR |
| `fix:` | PATCH |
| `feat!:` or `BREAKING CHANGE` | MAJOR |
| `docs:`, `chore:`, `refactor:` | None |

### 4. Repository Structure

We adopt the following top-level structure:

```
/
├── app/                    # Backend (FastAPI)
│   ├── ai/                 # AI integration layer
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── middleware/         # Request processing
│   ├── webhooks/           # Webhook handlers
│   └── logs/               # Logging utilities
├── frontend/               # Frontend (Next.js)
├── workers/                # Background workers (BullMQ)
├── supabase/               # Database & migrations
├── infra/                  # Infrastructure config
├── deploy/                 # Deployment guides
├── docs/                   # Documentation
├── ops/                    # Operational runbooks
├── security/               # Security documentation
├── repo/                   # Repository governance docs
├── scripts/                # Utility scripts
├── tests/                  # Test suites
├── ci/                     # CI outputs
├── grafana/                # Monitoring dashboards
└── .github/                # GitHub configuration
```

### 5. Documentation Standards

We require the following documentation structure:

**Root Level:**
- `README.md` - Project overview and quick start
- `MAINTAINERS.md` - Maintainer responsibilities
- `SECURITY.md` - Security policy
- `CONTRIBUTING.md` - Contribution guidelines
- `RELEASE.md` - Release process
- `CHANGELOG.md` - Version history

**Documentation Directory (`/docs`):**
- `architecture.md` - System architecture
- `staff-overview.md` - Staff-engineer narrative
- `engineering_principles.md` - Core engineering principles
- `branch_strategy.md` - Branch workflow
- `staff-repo-structure.md` - Staff-engineer repo guide
- `final-improvements.md` - Improvement roadmap
- `adr/` - Architecture Decision Records

**Operations Directory (`/ops`):**
- `runbook.md` - Operational procedures
- `verification.md` - Deployment verification
- `alerts.md` - Alert configurations
- `auto-scaler.md` - Scaling documentation
- `branch_protection.md` - Branch protection guide
- `oncall_playbook.md` - Incident response

### 6. CI/CD Pipeline Structure

We implement a comprehensive CI/CD pipeline with:
- Security scanning (gitleaks, detect-secrets, bandit)
- Backend tests with coverage
- Frontend tests and build
- Worker tests and build
- Infrastructure linting
- Integration tests
- Docker image builds
- Automated deployment to Railway

## Alternatives Considered

### Alternative 1: Multi-Maintainer Model

**Description:** Define multiple maintainers with area-specific ownership.

**Pros:**
- Distributes review burden
- Enables specialized expertise

**Cons:**
- Doesn't match current team size
- Adds coordination overhead
- Single owner is sufficient for current scale

**Decision:** Rejected - Premature for current team size. Can be added later.

### Alternative 2: GitFlow with Release Branches

**Description:** Use `develop` branch with `release/*` branches for releases.

**Pros:**
- Familiar to many developers
- Clear release isolation

**Cons:**
- Higher merge complexity
- Longer feedback loops
- Against trunk-based development best practices
- Not suitable for continuous deployment

**Decision:** Rejected - Trunk-based development better suits our continuous deployment model.

### Alternative 3: Minimal Governance

**Description:** Keep only essential documentation and automation.

**Pros:**
- Less overhead
- Faster initial setup

**Cons:**
- Knowledge trapped in individual
- Harder onboarding for future team members
- No audit trail for decisions
- Security and compliance gaps

**Decision:** Rejected - Staff-engineer level governance is appropriate for production SaaS.

## Consequences

### Positive

1. **Clear Ownership:** All code has defined ownership via CODEOWNERS
2. **Quality Enforcement:** Automated checks ensure code quality and security
3. **Knowledge Documentation:** Decisions and procedures are documented
4. **Onboarding Ready:** Future contributors have clear guides
5. **Compliance Ready:** Security and operational documentation supports SOC 2
6. **Release Clarity:** Semantic versioning and changelog provide clear release history

### Negative

1. **Initial Overhead:** Creating and maintaining documentation requires time
2. **Workflow Constraints:** Strict commit message format may feel restrictive
3. **Single Point of Review:** All changes require single owner approval

### Mitigations

- Documentation templates reduce creation overhead
- Commitlint provides clear error messages for format issues
- PR template guides contributors through requirements

## Implementation

1. Create governance files in `.github/`
2. Create documentation structure in `docs/`
3. Create operational documentation in `ops/`
4. Update README.md with governance summary
5. Enable branch protection rules in GitHub Settings (manual)
6. Communicate changes via PR

## References

- [Trunk Based Development](https://trunkbaseddevelopment.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

---

**Author:** Aditya Tiwari  
**Date:** 2026-02-20  
**Reviewers:** N/A (single owner)