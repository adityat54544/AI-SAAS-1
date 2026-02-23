/**
 * INFRA GUARDIAN - Log Analyzer
 * 
 * Intelligent log pattern detection and root cause analysis
 */

export type LogSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface LogPattern {
  pattern: RegExp;
  severity: LogSeverity;
  rootCause: string;
  service: 'frontend' | 'backend' | 'workers' | 'all';
  remediation: string;
}

export interface DetectedIssue {
  id: string;
  pattern: string;
  severity: LogSeverity;
  rootCause: string;
  service: string;
  remediation: string;
  firstSeen: Date;
  count: number;
}

// Predefined patterns for common issues
const LOG_PATTERNS: LogPattern[] = [
  // Frontend patterns
  {
    pattern: /Cannot find.*server\.js/,
    severity: 'critical',
    rootCause: 'Next.js standalone build missing server.js',
    service: 'frontend',
    remediation: 'Check Dockerfile standalone output configuration',
  },
  {
    pattern: /hydration.*error|hydration.*failed/,
    severity: 'error',
    rootCause: 'React hydration mismatch',
    service: 'frontend',
    remediation: 'Check for dynamic content or mismatched SSR/CSR',
  },
  {
    pattern: /ECONNREFUSED|fetch.*failed.*connection/,
    severity: 'error',
    rootCause: 'Backend API unreachable from frontend',
    service: 'frontend',
    remediation: 'Check NEXT_PUBLIC_API_URL and backend health',
  },
  {
    pattern: /Missing.*environment.*variable|undefined.*env/,
    severity: 'critical',
    rootCause: 'Missing required environment variable',
    service: 'frontend',
    remediation: 'Add missing env var to Railway variables',
  },
  {
    pattern: /Failed to load resource.*404/,
    severity: 'warning',
    rootCause: 'Missing static resource or API endpoint',
    service: 'frontend',
    remediation: 'Check build output and API routes',
  },
  
  // Backend patterns
  {
    pattern: /connection.*exhausted|pool.*exhausted/,
    severity: 'critical',
    rootCause: 'Database connection pool exhausted',
    service: 'backend',
    remediation: 'Increase pool size or check for connection leaks',
  },
  {
    pattern: /Redis.*timeout|connection.*refused.*redis/,
    severity: 'critical',
    rootCause: 'Redis connection failure',
    service: 'backend',
    remediation: 'Check Redis plugin status and credentials',
  },
  {
    pattern: /401.*unauthorized|authentication.*failed/,
    severity: 'warning',
    rootCause: 'Authentication failure',
    service: 'backend',
    remediation: 'Verify auth tokens and Supabase configuration',
  },
  {
    pattern: /rate.*limit|too many requests/,
    severity: 'warning',
    rootCause: 'Rate limit exceeded',
    service: 'backend',
    remediation: 'Check rate limit configuration',
  },
  {
    pattern: /validation.*error|422.*invalid/,
    severity: 'warning',
    rootCause: 'Request validation failed',
    service: 'backend',
    remediation: 'Check request payload and validation rules',
  },
  
  // Worker patterns
  {
    pattern: /queue.*backlog|jobs.*pending.*increasing/,
    severity: 'warning',
    rootCause: 'Worker queue backlog growing',
    service: 'workers',
    remediation: 'Scale up worker replicas',
  },
  {
    pattern: /retry.*storm|max.*retries.*exceeded/,
    severity: 'error',
    rootCause: 'Job retry storm detected',
    service: 'workers',
    remediation: 'Check job processing logic and external dependencies',
  },
  {
    pattern: /job.*failed.*analysis|analysis.*error/,
    severity: 'error',
    rootCause: 'Analysis job processing failure',
    service: 'workers',
    remediation: 'Check Gemini API and analysis logic',
  },
  {
    pattern: /gemini.*error|AI.*rate.*limit/,
    severity: 'warning',
    rootCause: 'AI service error or rate limit',
    service: 'workers',
    remediation: 'Check Gemini API quota and response times',
  },
];

class LogAnalyzer {
  private detectedIssues: Map<string, DetectedIssue> = new Map();
  private logBuffer: Array<{ timestamp: Date; service: string; message: string }> = [];
  private readonly maxBufferSize = 1000;

  /**
   * Analyze a single log line
   */
  analyzeLogLine(service: string, message: string): DetectedIssue | null {
    const timestamp = new Date();
    
    // Add to buffer
    this.logBuffer.push({ timestamp, service, message });
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer.shift();
    }
    
    // Check against patterns
    for (const logPattern of LOG_PATTERNS) {
      if (logPattern.pattern.test(message)) {
        // Check if service matches
        if (logPattern.service !== 'all' && logPattern.service !== service) {
          continue;
        }
        
        // Create or update detected issue
        const issueId = `${logPattern.rootCause}-${service}`;
        let issue = this.detectedIssues.get(issueId);
        
        if (issue) {
          issue.count++;
          issue.firstSeen = timestamp;
        } else {
          issue = {
            id: issueId,
            pattern: logPattern.pattern.source,
            severity: logPattern.severity,
            rootCause: logPattern.rootCause,
            service,
            remediation: logPattern.remediation,
            firstSeen: timestamp,
            count: 1,
          };
          this.detectedIssues.set(issueId, issue);
        }
        
        return issue;
      }
    }
    
    return null;
  }

  /**
   * Analyze multiple log lines
   */
  analyzeLogs(logs: Array<{ service: string; message: string }>): DetectedIssue[] {
    const issues: DetectedIssue[] = [];
    
    for (const log of logs) {
      const issue = this.analyzeLogLine(log.service, log.message);
      if (issue) {
        issues.push(issue);
      }
    }
    
    return issues;
  }

  /**
   * Get all currently tracked issues
   */
  getActiveIssues(): DetectedIssue[] {
    return Array.from(this.detectedIssues.values());
  }

  /**
   * Get issues by severity
   */
  getIssuesBySeverity(severity: LogSeverity): DetectedIssue[] {
    return this.getActiveIssues().filter(i => i.severity === severity);
  }

  /**
   * Get critical issues (require immediate attention)
   */
  getCriticalIssues(): DetectedIssue[] {
    return this.getIssuesBySeverity('critical');
  }

  /**
   * Clear resolved issues
   */
  clearResolvedIssues(): void {
    const critical = this.getCriticalIssues();
    
    // Keep critical issues, clear resolved ones
    for (const [id, issue] of this.detectedIssues) {
      if (issue.severity !== 'critical' && issue.severity !== 'error') {
        // Clear after 1 hour of no new occurrences
        const hourAgo = new Date(Date.now() - 3600000);
        if (issue.firstSeen < hourAgo) {
          this.detectedIssues.delete(id);
        }
      }
    }
  }

  /**
   * Get log buffer
   */
  getRecentLogs(count: number = 100): Array<{ timestamp: Date; service: string; message: string }> {
    return this.logBuffer.slice(-count);
  }

  /**
   * Get statistics
   */
  getStatistics(): {
    totalLogsProcessed: number;
    issuesDetected: number;
    criticalCount: number;
    errorCount: number;
    warningCount: number;
  } {
    const issues = this.getActiveIssues();
    
    return {
      totalLogsProcessed: this.logBuffer.length,
      issuesDetected: issues.length,
      criticalCount: issues.filter(i => i.severity === 'critical').length,
      errorCount: issues.filter(i => i.severity === 'error').length,
      warningCount: issues.filter(i => i.severity === 'warning').length,
    };
  }

  /**
   * Generate issue summary for reporting
   */
  generateIssueSummary(): string {
    const issues = this.getActiveIssues();
    
    if (issues.length === 0) {
      return 'No issues detected';
    }
    
    const critical = issues.filter(i => i.severity === 'critical');
    const errors = issues.filter(i => i.severity === 'error');
    const warnings = issues.filter(i => i.severity === 'warning');
    
    let summary = '## Issue Summary\n\n';
    
    if (critical.length > 0) {
      summary += `### 🚨 Critical (${critical.length})\n`;
      for (const issue of critical) {
        summary += `- [${issue.service}] ${issue.rootCause} (count: ${issue.count})\n`;
        summary += `  → ${issue.remediation}\n`;
      }
      summary += '\n';
    }
    
    if (errors.length > 0) {
      summary += `### ❌ Errors (${errors.length})\n`;
      for (const issue of errors) {
        summary += `- [${issue.service}] ${issue.rootCause} (count: ${issue.count})\n`;
      }
      summary += '\n';
    }
    
    if (warnings.length > 0) {
      summary += `### ⚠️ Warnings (${warnings.length})\n`;
      for (const issue of warnings.slice(0, 5)) {
        summary += `- [${issue.service}] ${issue.rootCause}\n`;
      }
    }
    
    return summary;
  }
}

export const logAnalyzer = new LogAnalyzer();
export default LogAnalyzer;
