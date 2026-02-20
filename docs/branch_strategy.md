# Branch Strategy

**Repository:** autodevops-ai-platform  
**Effective Date:** 2026-02-20  
**Status:** Active

---

## Overview

This repository enforces a **single-branch workflow** using only the `main` branch. This strategy eliminates branch sprawl, reduces merge complexity, and ensures all work is immediately integrated.

---

## Branch Model

### Active Branches

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Production-ready code | Full protection |

### No Long-Lived Branches

- ❌ No `develop` branch
- ❌ No `staging` branch
- ❌ No feature branches beyond PR lifecycle
- ❌ No release branches

---

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Workflow                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Create short-lived branch from main                     │
│            ↓                                                │
│  2. Make changes, commit                                    │
│            ↓                                                │
│  3. Open Pull Request                                       │
│            ↓                                                │
│  4. CI/CD runs automatically                                │
│            ↓                                                │
│  5. Code review & approval                                  │
│            ↓                                                │
│  6. Merge to main (squash or merge commit)                  │
│            ↓                                                │
│  7. Delete feature branch immediately                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Branch Lifecycle

1. **Create**: `git checkout -b feature/short-description main`
2. **Develop**: Make focused, atomic commits
3. **Push**: `git push origin feature/short-description`
4. **PR**: Open Pull Request with description
5. **Review**: Pass CI, get approval
6. **Merge**: Merge to main via GitHub UI
7. **Cleanup**: Delete branch after merge

---

## Branch Protection Rules (Recommended)

Configure in GitHub: Settings → Branches → Add Rule for `main`

### Required Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| Require pull request | ✅ Enabled | No direct pushes to main |
| Required approvals | 1+ | Code review required |
| Dismiss stale reviews | ✅ Enabled | Force re-review on changes |
| Require status checks | ✅ Enabled | CI must pass |
| Require branches to be up to date | ✅ Enabled | Merge conflicts resolved |
| Require signed commits | ⚠️ Optional | Commit verification |
| Include administrators | ⚠️ Optional | Admins follow same rules |

### Forbidden Actions

- ❌ Force push to main
- ❌ Delete main branch
- ❌ Direct commits to main (bypass PR)
- ❌ Merge without passing CI

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/
```

### Deployment Trigger

- Deployments trigger on push to `main`
- PR merges to `main` automatically deploy to staging
- Production deployments require additional approval

---

## Conventions

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/add-auth` |
| Fix | `fix/description` | `fix/login-error` |
| Docs | `docs/description` | `docs/api-reference` |
| Refactor | `refactor/description` | `refactor/auth-module` |

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## Emergency Procedures

### Hotfix Process

1. Create branch from `main`: `git checkout -b hotfix/critical-fix main`
2. Make minimal fix
3. Open PR with `hotfix` label
4. Expedited review and approval
5. Merge to `main`
6. Tag release: `git tag v1.x.x`

### Rollback

If a bad commit reaches `main`:

1. **Preferred**: Create a revert PR
2. **Emergency**: `git revert <commit-sha>`
3. **Never**: Force push to `main`

---

## Historical Context

### Branch Consolidation (2026-02-20)

The following branches were consolidated into `main`:

| Branch | Status | Action |
|--------|--------|--------|
| `master` | Merged | Deleted |
| `docs/improve-readme` | Merged | Deleted |
| `improve/ops-hardening` | Merged | Deleted |

All commits preserved in `main` via merge commit `f91233e`.

---

## FAQ

### Q: Why single-branch?

A: Eliminates branch maintenance overhead, ensures immediate integration testing, simplifies deployment pipeline.

### Q: How do I work on multiple features?

A: Create separate short-lived branches. Complete one at a time or use `git stash` to switch context.

### Q: What about releases?

A: Use Git tags for releases. No release branches needed.

### Q: How do I handle long-running features?

A: Break into smaller, mergeable chunks. Feature flags can hide incomplete work.

---

## Enforcement

This strategy is enforced by:

1. **GitHub Branch Protection**: Technical enforcement
2. **CI/CD Pipeline**: Automated checks
3. **Code Review**: Human enforcement
4. **Documentation**: This guide

Violations require explicit approval from repository administrators.

---

## References

- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)