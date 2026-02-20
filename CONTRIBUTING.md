# Contributing to AutoDevOps AI Platform

Thank you for your interest in contributing to the AutoDevOps AI Platform! This document provides guidelines and instructions for contributing.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and diverse perspectives
- Accept constructive criticism gracefully
- Focus on what is best for the community and project
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Initial Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/AI-SAAS-1.git
cd AI-SAAS-1

# 3. Add upstream remote
git remote add upstream https://github.com/adityat54544/AI-SAAS-1.git

# 4. Create virtual environment for backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Install frontend dependencies
cd frontend && npm install && cd ..

# 6. Install worker dependencies
cd workers && npm install && cd ..

# 7. Set up pre-commit hooks
pip install pre-commit
pre-commit install
```

### Environment Configuration

1. Copy `.env.example` to `.env`
2. Configure required environment variables
3. Never commit real credentials

---

## Development Workflow

### Branch Strategy

This project uses **trunk-based development**:

- `main` is the only permanent branch
- All changes come through pull requests
- Feature branches are short-lived (< 3 days)
- Delete branches after merge

### Branch Naming Convention

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/add-auth` |
| Fix | `fix/description` | `fix/login-error` |
| Docs | `docs/description` | `docs/api-reference` |
| Refactor | `refactor/description` | `refactor/auth-module` |
| Chore | `chore/description` | `chore/update-deps` |

### Workflow Steps

```bash
# 1. Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 4. Push to your fork
git push origin feature/my-feature

# 5. Open Pull Request on GitHub

# 6. After merge, delete the branch
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

---

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | None |
| `style` | Code style (formatting) | None |
| `refactor` | Code refactoring | None |
| `test` | Adding/updating tests | None |
| `chore` | Maintenance tasks | None |
| `ci` | CI/CD changes | None |
| `perf` | Performance improvement | PATCH |
| `revert` | Revert previous commit | Varies |
| `build` | Build system changes | None |

### Examples

```bash
# Good commits
git commit -m "feat: add user authentication"
git commit -m "fix(api): resolve timeout issue"
git commit -m "docs(readme): update installation steps"
git commit -m "chore!: update minimum Python version to 3.11"

# Bad commits (avoid these)
git commit -m "fixed stuff"
git commit -m "WIP"
git commit -m "update"
```

### Breaking Changes

For breaking changes, add `!` after the type or include `BREAKING CHANGE:` in the footer:

```bash
git commit -m "feat!: redesign API response format"
# or
git commit -m "feat: redesign API response format

BREAKING CHANGE: API response format changed from v1 to v2"
```

---

## Pull Request Process

### Before Opening a PR

- [ ] Code compiles without errors
- [ ] All tests pass locally
- [ ] Pre-commit hooks pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions

### PR Checklist

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests added/updated
- [ ] CHANGELOG.md updated (if applicable)
```

### Review Process

1. **Automated Checks**: CI must pass
2. **Code Review**: Maintainer review required
3. **Discussion**: Address any feedback
4. **Approval**: At least one approval needed
5. **Merge**: Squash and merge (default)

### Merge Requirements

- All CI checks must pass
- At least one approval from a maintainer
- No unresolved conversations
- Branch is up to date with `main`

---

## Code Standards

### Python (Backend)

- **Formatter**: Ruff (replaces Black)
- **Linter**: Ruff
- **Type Checking**: MyPy
- **Import Order**: isort (via Ruff)

```bash
# Format code
ruff format app/

# Lint code
ruff check app/ --fix

# Type check
mypy app/ --ignore-missing-imports
```

### TypeScript (Frontend/Workers)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checking**: TypeScript compiler

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### General Guidelines

- Write self-documenting code
- Keep functions small and focused
- Use meaningful variable names
- Add comments for complex logic
- Follow DRY principles

---

## Testing

### Running Tests

```bash
# Backend tests
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend tests
cd frontend && npm test

# Workers tests
cd workers && npm test

# Integration tests
pytest tests/integration/ -v
```

### Test Requirements

- All new code requires tests
- Maintain or improve code coverage
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical paths

### Test Naming

```python
# Pattern: test_<function>_<scenario>_<expected_result>
def test_authenticate_user_valid_credentials_returns_token():
    ...

def test_authenticate_user_invalid_credentials_raises_error():
    ...
```

---

## Documentation

### Types of Documentation

| Type | Location | Purpose |
|------|----------|---------|
| README | `/README.md` | Project overview |
| Architecture | `/docs/architecture.md` | System design |
| API | `/docs/api/` | API documentation |
| ADRs | `/docs/adr/` | Architecture decisions |
| Runbooks | `/ops/` | Operational procedures |

### Updating Documentation

- Update README.md for new features
- Update CHANGELOG.md for user-facing changes
- Create ADR for architectural decisions
- Update API docs for endpoint changes

---

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Pull Request Comments**: For code-specific questions

---

## Recognition

Contributors are recognized through:

- GitHub contributor graph
- Acknowledgment in CHANGELOG.md for significant contributions
- Potential maintainer status for sustained contributions

---

Thank you for contributing! 🎉