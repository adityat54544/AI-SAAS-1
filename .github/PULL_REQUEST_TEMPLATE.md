---
name: Pull Request
about: Submit changes for review
title: ''
labels: ''
assignees: ''
---

## Description

<!-- Provide a clear, concise description of the changes -->

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] 🧹 Chore (maintenance, dependencies, CI/CD)

## Trunk-Based Development Compliance

This repository follows a **single-branch workflow**. All changes must comply with the following requirements:

### Branch Compliance

- [ ] This branch is **short-lived** (< 3 days old)
- [ ] This branch was created from `main`
- [ ] This branch will be **deleted immediately after merge**

### Change Size

- [ ] This PR contains **focused, atomic changes** (ideally < 400 lines changed)
- [ ] If this PR is large, I have explained why it cannot be split

## Pre-Merge Safety Checks

### CI/CD Requirements

- [ ] All CI checks have **passed** (tests, linting, security scan)
- [ ] No new security vulnerabilities introduced
- [ ] Code coverage has not decreased significantly

### Code Quality

- [ ] Self-review completed
- [ ] Code follows project conventions (see `docs/branch_strategy.md`)
- [ ] Commit messages follow conventional commits format

### Documentation

- [ ] Relevant documentation updated (if applicable)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Environment variables documented in `.env.example` (if new vars added)

## Testing

<!-- Describe the tests you ran to verify your changes -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

### Test Results

<!-- Paste relevant test output or summarize test coverage -->

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Related Issues

<!-- Link any related issues using #issue-number -->

Fixes #

## Post-Merge Actions

<!-- List any actions needed after this PR is merged -->

- [ ] No post-merge actions required
- [ ] Post-merge actions documented below:

<!-- 
Example post-merge actions:
- Monitor production logs for X
- Verify deployment succeeded
- Update external documentation
-->

---

## For Reviewers

### Review Checklist

- [ ] Code is readable and maintainable
- [ ] No obvious security issues
- [ ] Tests are appropriate and comprehensive
- [ ] Documentation is clear and complete
- [ ] Change aligns with trunk-based development principles

### Merge Requirements

**This PR can only be merged when:**
1. All CI checks pass ✅
2. At least one approval from a maintainer ✅
3. Branch is up-to-date with `main` ✅
4. No unresolved conversations ✅

---

**Remember:** After merge, this branch will be automatically deleted. Ensure all important content has been merged.