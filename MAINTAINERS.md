# Maintainers

This document defines the maintenance team and responsibilities for the AutoDevOps AI Platform.

---

## Active Maintainers

| Name | Role | GitHub | Focus Areas |
|------|------|--------|-------------|
| Aditya Tiwari | Founder & Lead Engineer | [@adityat54544](https://github.com/adityat54544) | Architecture, Backend, AI, Security, Infrastructure |

---

## Maintainer Responsibilities

### Code Review
- Review pull requests within 48 hours
- Ensure code quality, security, and architectural consistency
- Provide constructive feedback
- Merge approved PRs after all checks pass

### Release Management
- Follow semantic versioning (see [RELEASE.md](RELEASE.md))
- Create release tags and GitHub releases
- Update CHANGELOG.md for each release
- Coordinate deployment activities

### Security
- Respond to security reports within 24 hours
- Coordinate security fixes and disclosures
- Review and approve security-related changes
- Maintain security documentation

### Community
- Respond to issues and discussions
- Triage and label incoming issues
- Provide support and guidance to contributors
- Maintain contributor documentation

---

## Code Ownership

Code ownership is defined in [`.github/CODEOWNERS`](.github/CODEOWNERS). All code changes require approval from the designated owner.

### Ownership Structure

```
*                           @adityat54544    (default owner)
/app/                       @adityat54544    (backend)
/frontend/                  @adityat54544    (frontend)
/workers/                   @adityat54544    (workers)
/infra/                     @adityat54544    (infrastructure)
/.github/                   @adityat54544    (ci/cd)
/supabase/                  @adityat54544    (database)
/docs/                      @adityat54544    (documentation)
/tests/                     @adityat54544    (testing)
```

---

## Decision Making

### Technical Decisions
- Major architectural changes require ADR (Architecture Decision Record)
- Minor changes can be approved by maintainer review
- Breaking changes require explicit discussion

### Emergency Fixes
- Critical security fixes can be merged immediately
- Post-merge review required within 24 hours
- Incident documentation required

---

## On-Call & Incident Response

For incident response procedures, see [ops/oncall_playbook.md](ops/oncall_playbook.md).

### Escalation Path
1. Create GitHub issue with `critical` label
2. Contact maintainer via GitHub mention
3. For security issues, follow [SECURITY.md](SECURITY.md)

---

## Becoming a Maintainer

Currently, this is a single-maintainer project. Contributions are welcome, and maintainer status may be extended to significant contributors who:

1. Have made substantial, high-quality contributions
2. Have demonstrated understanding of the codebase and architecture
3. Have consistently participated in code review and discussions
4. Have shown commitment to the project's long-term success

---

## Stepping Down

If a maintainer needs to step down:
1. Notify other maintainers via GitHub issue or discussion
2. Update MAINTAINERS.md and CODEOWNERS
3. Ensure knowledge transfer for owned components

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Aditya Tiwari | Initial maintainers document |