# Testing Coverage Guide

**Date:** 2026-02-21  
**Status:** Active

## Overview

This guide provides comprehensive instructions for running tests, interpreting coverage reports, and maintaining test quality standards across the AutoDevOps AI Platform.

## Coverage Requirements

| Service | Minimum Coverage | Target Coverage |
|---------|-----------------|-----------------|
| Frontend | 70% | 80% |
| Workers | 80% | 90% |
| Backend | 70% | 80% |

## Running Tests

### Frontend (Vitest)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run tests without coverage
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run tests with interactive UI
npm run test:ui
```

### Workers (Vitest)

```bash
# Navigate to workers directory
cd workers

# Install dependencies
npm install

# Run tests without coverage
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run tests with interactive UI
npm run test:ui
```

### Backend (pytest)

```bash
# Run tests without coverage
ENVIRONMENT=test pytest tests/ -v

# Run tests with coverage
ENVIRONMENT=test pytest tests/ -v --cov=app --cov-report=term-missing

# Run tests with HTML coverage report
ENVIRONMENT=test pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
ENVIRONMENT=test pytest tests/test_basic.py -v
```

## Coverage Reports

### Understanding Coverage Output

Vitest provides coverage in multiple formats:

- **text**: Console output showing coverage percentages
- **html**: Interactive HTML report in `coverage/index.html`
- **lcov**: Standard format for CI integration (Codecov)

### Coverage Metrics Explained

| Metric | Description |
|--------|-------------|
| **Statements** | Percentage of executable statements covered |
| **Branches** | Percentage of control flow branches executed |
| **Functions** | Percentage of functions called |
| **Lines** | Percentage of executable lines covered |

### Viewing HTML Reports

```bash
# Frontend
cd frontend && npm run test:coverage
open coverage/index.html  # macOS
start coverage/index.html  # Windows
xdg-open coverage/index.html  # Linux

# Workers
cd workers && npm run test:coverage
open coverage/index.html

# Backend
ENVIRONMENT=test pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Mock Services

### Frontend Mock Services (MSW)

The frontend uses Mock Service Worker (MSW) for API mocking:

**Configuration Files:**
- `frontend/src/test/setup.ts` - Test setup and lifecycle
- `frontend/src/test/mocks/handlers.ts` - API mock handlers
- `frontend/src/test/mocks/server.ts` - MSW server setup

**Adding New Mock Handlers:**

```typescript
// In frontend/src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // Add new handler
  http.get(`${API_URL}/api/new-endpoint`, () => {
    return HttpResponse.json({
      // Response data
    })
  }),
  // ... existing handlers
]
```

### Backend Mock Services

The backend uses mock classes for deterministic testing:

**Configuration File:**
- `tests/mocks/github_service.py` - GitHub service mock

**Using Mocks in Tests:**

```python
from tests.mocks.github_service import MockGitHubService

def test_repository_fetch():
    mock_service = MockGitHubService()
    result = await mock_service.get_repository("test-token", "owner/repo")
    assert result["name"] == "test-repo"
```

## Coverage Exclusions

### Frontend Exclusions

The following are excluded from coverage:

- Configuration files (`*.config.*`)
- Type definitions (`*.d.ts`)
- Next.js app router files (`src/app/**`)
- Test utilities (`src/test/**`)

### Workers Exclusions

- Configuration files (`*.config.*`)
- Type definitions (`*.d.ts`)
- Build output (`dist/**`)
- Test files (`tests/**`)

### Modifying Exclusions

Edit the respective `vitest.config.ts`:

```typescript
coverage: {
  exclude: [
    // Add or modify exclusions
    '**/*.config.*',
    // ...
  ]
}
```

## CI Integration

Coverage reports are automatically uploaded to Codecov:

- Frontend: `frontend/coverage/lcov.info` with `frontend` flag
- Workers: `workers/coverage/lcov.info` with `workers` flag
- Backend: `coverage.xml`

View coverage trends at your Codecov dashboard.

## Best Practices

### Writing Testable Code

1. **Pure Functions**: Prefer pure functions for easier testing
2. **Dependency Injection**: Inject dependencies for mocking
3. **Small Modules**: Keep functions and modules focused
4. **Clear Interfaces**: Define clear interfaces between components

### Achieving Good Coverage

1. **Test Happy Paths**: Verify expected behavior works
2. **Test Edge Cases**: Handle boundary conditions
3. **Test Error Handling**: Verify error responses
4. **Test Integration Points**: Mock external dependencies

### Coverage Anti-Patterns to Avoid

1. **Testing Implementation Details**: Focus on behavior, not implementation
2. **Excessive Mocking**: Mock only external dependencies
3. **Coverage Chasing**: Write meaningful tests, not just for coverage
4. **Ignoring Failed Tests**: Never commit with failing tests

## Troubleshooting

### Tests Pass Locally but Fail in CI

- Check environment variables are set
- Verify all external APIs are mocked
- Ensure consistent Node.js/Python versions

### Low Coverage on Specific Files

- Review file for untested branches
- Add tests for error handling paths
- Check for dead code that should be removed

### Coverage Report Not Generated

- Verify `@vitest/coverage-v8` is installed
- Check disk space for HTML reports
- Ensure write permissions in coverage directory

## Support

For questions or issues with testing:

1. Check this documentation
2. Review `docs/ci-stabilization.md` for CI-specific issues
3. Consult `CONTRIBUTING.md` for contribution guidelines