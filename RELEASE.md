# Release Process

This document describes the release process, semantic versioning strategy, and changelog management for the AutoDevOps AI Platform.

---

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/). Version numbers follow the format `MAJOR.MINOR.PATCH`.

### Version Components

| Component | When to Increment | Example |
|-----------|-------------------|---------|
| **MAJOR** | Breaking changes | 1.0.0 → 2.0.0 |
| **MINOR** | New features (backward compatible) | 1.0.0 → 1.1.0 |
| **PATCH** | Bug fixes (backward compatible) | 1.0.0 → 1.0.1 |

### Version Determination from Commits

Commit types automatically determine version bumps:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | MINOR | 1.0.0 → 1.1.0 |
| `fix:` | PATCH | 1.0.0 → 1.0.1 |
| `feat!:` or `BREAKING CHANGE` | MAJOR | 1.0.0 → 2.0.0 |
| `docs:`, `chore:`, `refactor:`, `test:` | None | N/A |
| `perf:` | PATCH | 1.0.0 → 1.0.1 |

### Pre-release Versions

Pre-release versions follow this format: `MAJOR.MINOR.PATCH-<identifier>`

| Identifier | Purpose | Example |
|------------|---------|---------|
| `-alpha.N` | Early testing | 2.0.0-alpha.1 |
| `-beta.N` | Feature complete | 2.0.0-beta.1 |
| `-rc.N` | Release candidate | 2.0.0-rc.1 |

---

## Release Workflow

### 1. Prepare for Release

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Run full test suite
pytest tests/ -v --cov=app

# Run linting
ruff check app/ --fix
npm run lint --prefix frontend
npm run lint --prefix workers
```

### 2. Update Changelog

Update `CHANGELOG.md` with all changes since the last release:

```markdown
## [1.1.0] - 2026-02-20

### Added
- New AI model routing with fallback support
- User preference dashboard

### Changed
- Improved rate limiting algorithm

### Fixed
- OAuth token refresh edge case

### Security
- Updated dependency versions
```

### 3. Create Release Tag

```bash
# Create annotated tag
git tag -a v1.1.0 -m "Release v1.1.0: AI Model Routing"

# Push tag to remote
git push origin v1.1.0
```

### 4. Create GitHub Release

1. Go to [Releases](https://github.com/adityat54544/AI-SAAS-1/releases)
2. Click "Draft a new release"
3. Select the tag
4. Title: `v1.1.0 - Brief Description`
5. Copy CHANGELOG section for this release
6. Publish release

### 5. Verify Deployment

- Monitor CI/CD pipeline completion
- Verify production deployment
- Run smoke tests
- Check monitoring dashboards

---

## Changelog Management

### CHANGELOG.md Format

We follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Feature that is not yet released

## [1.1.0] - 2026-02-20

### Added
- New feature description

### Changed
- Change description

### Deprecated
- Deprecated feature description

### Removed
- Removed feature description

### Fixed
- Bug fix description

### Security
- Security fix description

## [1.0.0] - 2026-01-15
...
```

### Changelog Categories

| Category | Description |
|----------|-------------|
| **Added** | New features |
| **Changed** | Changes to existing features |
| **Deprecated** | Features to be removed |
| **Removed** | Features removed in this release |
| **Fixed** | Bug fixes |
| **Security** | Security-related changes |

### What to Include

- User-facing changes
- Breaking changes (highlight prominently)
- Security fixes
- Dependency updates with security implications
- Deprecation notices

### What Not to Include

- Internal refactoring without user impact
- Test improvements
- Documentation typos
- Minor code style changes

---

## Release Automation

### GitHub Actions (Future)

When implemented, releases will be automated:

```yaml
# .github/workflows/release.yml (future)
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build
        run: |
          docker build -t app:${{ github.ref_name }}
      
      - name: Deploy
        run: |
          railway deploy
```

### Current Manual Steps

Until automation is complete:

1. Create tag locally
2. Push tag to GitHub
3. GitHub Actions builds and pushes Docker images
4. Railway deploys from `main` branch
5. Verify deployment health

---

## Breaking Changes

### Definition

A breaking change is any change that:

- Removes or renames an API endpoint
- Changes required request/response formats
- Removes or changes required environment variables
- Changes database schema in incompatible ways
- Removes or changes command-line arguments

### Communicating Breaking Changes

1. **In Commit Message**:
   ```
   feat!: redesign API response format
   
   BREAKING CHANGE: The /api/analyze endpoint now returns
   results in a new format. Clients must update to v2 format.
   Migration guide: docs/migration/v2-api.md
   ```

2. **In CHANGELOG.md**:
   ```markdown
   ### BREAKING CHANGES
   - `GET /api/analyze` response format changed
   - `SUPABASE_URL` environment variable is now required
   ```

3. **In Release Notes**:
   - Add "⚠️ Breaking Changes" section at top
   - Provide migration instructions
   - Link to documentation

### Deprecation Policy

1. Announce deprecation in CHANGELOG and documentation
2. Support deprecated feature for at least 2 minor releases
3. Add runtime warnings for deprecated features
4. Remove in next MAJOR release

---

## Hotfix Process

For critical production issues:

### 1. Identify Issue

- Confirm severity (Critical/High)
- Document reproduction steps
- Identify affected versions

### 2. Create Hotfix Branch

```bash
# Create from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue

# Make minimal fix
git commit -m "fix: resolve critical authentication bug"

# Push and create PR
git push origin hotfix/critical-issue
```

### 3. Expedited Review

- Maintainer reviews immediately
- CI must pass
- Merge to main

### 4. Release Hotfix

```bash
# Tag hotfix release
git tag -a v1.0.1 -m "Hotfix: Critical auth fix"
git push origin v1.0.1

# Update CHANGELOG
# Create GitHub release
```

---

## Rollback Procedure

If a release causes issues:

### 1. Immediate Rollback

```bash
# Railway rollback
railway rollback

# Or deploy previous version
railway up --service autodevops-api --tag v1.0.0
```

### 2. Document Issue

- Create GitHub issue
- Document reproduction steps
- Estimate fix timeline

### 3. Communicate

- Update status page
- Notify affected users
- Post incident summary

---

## Release Checklist

### Pre-Release

- [ ] All tests pass
- [ ] Linting passes
- [ ] Security scans pass
- [ ] CHANGELOG.md updated
- [ ] Version bumped in code (if applicable)
- [ ] Documentation updated
- [ ] Breaking changes documented

### Release

- [ ] Tag created
- [ ] Tag pushed to GitHub
- [ ] GitHub release created
- [ ] CI/CD pipeline successful
- [ ] Deployment successful

### Post-Release

- [ ] Health checks pass
- [ ] Smoke tests pass
- [ ] Monitoring dashboards checked
- [ ] Team notified

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2026-02-15 | Initial release |
| 1.0.0 | TBD | Production ready |

---

## Questions?

For questions about releases:

- **GitHub Issues**: General release questions
- **Security**: Follow [SECURITY.md](SECURITY.md)
- **Maintainer**: @adityat54544

---

*This document is updated as the release process evolves.*