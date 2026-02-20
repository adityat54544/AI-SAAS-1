# Security Policy

**AutoDevOps AI Platform**

This document outlines the security policy, vulnerability disclosure process, and security best practices for the AutoDevOps AI Platform.

---

## Supported Versions

| Version | Supported | Status |
|---------|-----------|--------|
| `main` branch | ✅ Yes | Active development |
| Latest release | ✅ Yes | Production support |
| Older releases | ❌ No | End of life |

We only support security fixes for the latest release and the `main` branch.

---

## Reporting a Vulnerability

### How to Report

**Do NOT create a public GitHub issue for security vulnerabilities.**

Instead, please report security issues through one of the following channels:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security Advisories](https://github.com/adityat54544/AI-SAAS-1/security/advisories) page
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

2. **Email** (Alternative)
   - Send an email to the maintainer with subject: `[SECURITY] AutoDevOps AI Platform`
   - Include the GitHub issue in your email for tracking

### What to Include

Please provide the following information:

- **Vulnerability Type**: (e.g., XSS, SQL Injection, Authentication Bypass)
- **Affected Component**: (e.g., API, Frontend, Workers)
- **Description**: Clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Proof of Concept**: If available, include a minimal PoC
- **Impact Assessment**: Potential impact if exploited
- **Suggested Fix**: If you have suggestions for remediation

### Response Timeline

| Stage | Expected Timeline |
|-------|-------------------|
| Initial Response | Within 24 hours |
| Vulnerability Confirmation | Within 72 hours |
| Fix Development | Based on severity |
| Security Advisory Published | After fix is released |

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **Critical** | Remote code execution, data breach, authentication bypass | 24 hours |
| **High** | Privilege escalation, significant data exposure | 72 hours |
| **Medium** | Limited data exposure, requires user interaction | 1 week |
| **Low** | Minor security issues, best practice improvements | 2 weeks |

---

## Security Best Practices

### For Contributors

1. **Never commit secrets**
   - Use `.env.example` for documentation
   - Never include real credentials in code
   - Use secret managers in production

2. **Follow secure coding guidelines**
   - Validate all input data
   - Use parameterized queries
   - Implement proper error handling
   - Sanitize user-generated content

3. **Code review for security**
   - Review all PRs for security implications
   - Check for exposed credentials
   - Verify authentication and authorization

### For Deployment

1. **Environment Variables**
   - All secrets must be stored in environment variables
   - Use Railway environment variables for production
   - Rotate secrets regularly (see rotation scripts in `/scripts`)

2. **Access Control**
   - GitHub OAuth tokens are encrypted before storage
   - Row-Level Security (RLS) enforces tenant isolation
   - Rate limiting prevents abuse

3. **Encryption**
   - OAuth tokens encrypted with AES-256-GCM
   - TLS 1.3 enforced for all connections
   - Database encryption at rest enabled

---

## Security Features

### Authentication & Authorization

| Feature | Implementation |
|---------|----------------|
| OAuth 2.0 | GitHub OAuth integration |
| JWT Sessions | HS256 signed, 1-hour expiry |
| Row-Level Security | PostgreSQL RLS policies |
| Token Encryption | AES-256-GCM with random IV |

### Network Security

| Feature | Implementation |
|---------|----------------|
| HTTPS | TLS 1.3 enforced |
| CORS | Whitelisted origins only |
| Rate Limiting | Redis-backed slowapi |
| DDoS Protection | Railway infrastructure |

### Application Security

| Feature | Implementation |
|---------|----------------|
| Input Validation | Pydantic models |
| SQL Injection | Parameterized queries |
| XSS Prevention | Output encoding |
| CSRF Protection | Same-site cookies |
| Webhook Verification | HMAC-SHA256 |

### Security Scanning

| Tool | Purpose | Frequency |
|------|---------|-----------|
| Gitleaks | Secret detection | Every commit |
| detect-secrets | Secret scanning | Every commit |
| Bandit | Python SAST | CI pipeline |
| Safety | Dependency check | CI pipeline |

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                       │
│ - HTTPS everywhere (Vercel/Railway managed)                    │
│ - CORS restrictions                                             │
│ - Rate limiting (per-user and per-IP)                          │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Authentication                                         │
│ - GitHub OAuth2 with PKCE                                       │
│ - JWT sessions with short expiry (1hr)                          │
│ - HttpOnly, Secure cookies                                      │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Authorization                                          │
│ - Row-Level Security in database                                │
│ - Organization-based tenant isolation                           │
│ - API endpoint permission checks                                │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Data Protection                                        │
│ - AES-256-GCM encryption for OAuth tokens                       │
│ - HMAC-SHA256 webhook verification                              │
│ - Secrets via environment variables only                         │
├─────────────────────────────────────────────────────────────────┤
│ Layer 5: Audit & Monitoring                                     │
│ - Structured logging with correlation IDs                       │
│ - Sentry error tracking                                         │
│ - GitHub audit log integration                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Incident Response

### Security Incident Process

1. **Detection**: Alert received via monitoring or report
2. **Assessment**: Determine severity and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and patch vulnerability
5. **Recovery**: Restore services and verify integrity
6. **Post-Mortem**: Document and improve processes

### Incident Contact

For active security incidents:
1. Create a private security advisory on GitHub
2. The maintainer will acknowledge within 24 hours
3. Coordinate response through secure channels

---

## Security Changelog

| Date | Issue | Severity | Resolution |
|------|-------|----------|------------|
| (Initial) | N/A | N/A | Security documentation created |

---

## Additional Resources

- [Security Report](security/report.md) - Detailed security assessment
- [Operations Runbook](ops/runbook.md) - Incident procedures
- [Architecture Documentation](docs/architecture.md) - System design

---

## Acknowledgments

We appreciate responsible disclosure of security vulnerabilities. Contributors who report valid security issues will be acknowledged (with permission) in our security advisories.

---

## Contact

**Security Contact**: Aditya Tiwari ([@adityat54544](https://github.com/adityat54544))

For non-security issues, please use [GitHub Issues](https://github.com/adityat54544/AI-SAAS-1/issues).

---

*This security policy is reviewed and updated regularly. Last updated: 2026-02-20*