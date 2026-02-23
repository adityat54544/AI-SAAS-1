/**
 * INFRA GUARDIAN - Main Orchestrator
 * 
 * Autonomous SRE System - Main Entry Point
 * 
 * This module orchestrates all Guardian components:
 * - Health monitoring
 * - Log analysis
 * - Anomaly detection
 * - Auto-scaling
 * - Incident tracking
 * - Alerting (Slack, Discord, PagerDuty)
 * - Railway API integration
 * - Daily reporting
 */

import { guardianConfig } from './config';
import { healthMonitor, SystemHealth, ServiceStatus } from './health-monitor';
import { logAnalyzer, DetectedIssue } from './log-analyzer';
import { autoScaler, ScalingMetrics } from './auto-scaler';
import { railwayClient } from './railway-client';
import { alertManager, AlertConfig } from './alerting';

export type GuardianState = 'initializing' | 'running' | 'degraded' | 'critical' | 'stopped';

export interface GuardianStatus {
  state: GuardianState;
  lastCheck: Date | null;
  systemHealth: SystemHealth | null;
  activeIssues: DetectedIssue[];
  scalingMetrics: ScalingMetrics[];
  uptime: number;
  railwayConnected: boolean;
}

export interface GuardianConfig {
  checkIntervalMs: number;
  enableAutoScaling: boolean;
  enableAutoPatch: boolean;
  railwayToken?: string;
  railwayProjectId?: string;
}

class GuardianOrchestrator {
  private state: GuardianState = 'initializing';
  private lastCheck: Date | null = null;
  private startTime: Date = new Date();
  private intervalId: NodeJS.Timeout | null = null;
  private config: GuardianConfig;

  constructor(config?: Partial<GuardianConfig>) {
    this.config = {
      checkIntervalMs: guardianConfig.healthCheck.intervalMs,
      enableAutoScaling: true,
      enableAutoPatch: true,
      ...config,
    };
  }

  /**
   * Initialize Guardian with Railway and Alerting
   */
  async initialize(
    alertConfig?: AlertConfig,
    railwayToken?: string,
    railwayProjectId?: string
  ): Promise<void> {
    console.log('🛡️ INFRA GUARDIAN initializing...');

    // Configure alerting
    if (alertConfig) {
      alertManager.configure(alertConfig);
      console.log('   ✓ Alerting configured');
    }

    // Initialize Railway client
    if (railwayToken) {
      railwayClient.initialize(railwayToken, railwayProjectId);
      const connected = await railwayClient.checkConnection();
      if (connected) {
        console.log('   ✓ Railway API connected');
        
        // Get project info
        if (railwayProjectId) {
          const services = await railwayClient.getServices();
          console.log(`   ✓ Found ${services.length} services in project`);
        }
      } else {
        console.warn('   ⚠ Railway API connection failed');
      }
    }

    console.log('🛡️ INFRA GUARDIAN initialized\n');
  }

  /**
   * Start the Guardian monitoring loop
   */
  start(): void {
    if (this.intervalId) {
      console.log('Guardian is already running');
      return;
    }

    this.state = 'initializing';
    console.log('🛡️ INFRA GUARDIAN starting...');
    console.log(`   Check interval: ${this.config.checkIntervalMs}ms`);
    console.log(`   Auto-scaling: ${this.config.enableAutoScaling ? 'enabled' : 'disabled'}`);
    console.log(`   Auto-patch: ${this.config.enableAutoPatch ? 'enabled' : 'disabled'}`);

    // Run initial check
    this.runHealthCheck();

    // Set up interval
    this.intervalId = setInterval(
      () => this.runHealthCheck(),
      this.config.checkIntervalMs
    );

    this.state = 'running';
    console.log('🛡️ INFRA GUARDIAN is now running\n');
  }

  /**
   * Stop the Guardian monitoring loop
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.state = 'stopped';
    console.log('🛡️ INFRA GUARDIAN stopped');
  }

  /**
   * Run a single health check cycle
   */
  async runHealthCheck(): Promise<GuardianStatus> {
    this.lastCheck = new Date();
    
    console.log(`\n🔍 [${this.lastCheck.toISOString()}] Running health check...`);

    let railwayConnected = false;
    let servicesWithStatus: Array<{ service: unknown; deployment: unknown }> = [];

    // Try to get Railway service status
    try {
      if (railwayClient.getProjectId()) {
        servicesWithStatus = await railwayClient.getAllServicesWithStatus();
        railwayConnected = true;
        console.log(`   Railway services: ${servicesWithStatus.length}`);
      }
    } catch (error) {
      console.warn('   Could not fetch Railway status:', error);
    }

    try {
      // 1. Check all services
      const systemHealth = await healthMonitor.checkAllServices();
      console.log(`   System health: ${systemHealth.overall}`);

      // 2. Alert on unhealthy services
      for (const service of systemHealth.services) {
        if (service.status !== 'healthy') {
          await alertManager.alertServiceHealth(service);
        }
      }

      // 3. Analyze logs (simulated - in production, would fetch from Railway)
      const activeIssues = logAnalyzer.getActiveIssues();
      if (activeIssues.length > 0) {
        console.log(`   Active issues: ${activeIssues.length}`);
      }

      // 4. Get scaling recommendations
      let scalingMetrics: ScalingMetrics[] = [];
      if (this.config.enableAutoScaling) {
        // In production, get actual queue depth from Redis
        const queueDepth = 0; // Would query Redis
        const recommendations = await autoScaler.getAllScalingRecommendations(
          queueDepth,
          2, // Current worker replicas
          1   // Current API replicas
        );
        scalingMetrics = recommendations;

        // Alert on scaling actions
        for (const metric of recommendations) {
          await alertManager.alertScaling(metric.recommendation);
        }
      }

      // 5. Alert on system health
      if (systemHealth.overall !== 'healthy') {
        await alertManager.alertSystemHealth(systemHealth);
      }

      // 6. Update state based on health
      this.updateState(systemHealth, activeIssues);

      // 7. Log summary
      this.logSummary(systemHealth, activeIssues);

      return {
        state: this.state,
        lastCheck: this.lastCheck,
        systemHealth,
        activeIssues,
        scalingMetrics,
        uptime: Date.now() - this.startTime.getTime(),
        railwayConnected,
      };
    } catch (error) {
      console.error('   Health check failed:', error);
      this.state = 'critical';
      
      // Alert on critical failure
      await alertManager.sendAlert(
        'critical',
        'Guardian Health Check Failed',
        `Health check error: ${error}`
      );
      
      return {
        state: this.state,
        lastCheck: this.lastCheck,
        systemHealth: null,
        activeIssues: [],
        scalingMetrics: [],
        uptime: Date.now() - this.startTime.getTime(),
        railwayConnected: false,
      };
    }
  }

  /**
   * Update Guardian state based on health and issues
   */
  private updateState(health: SystemHealth, issues: DetectedIssue[]): void {
    const criticalIssues = issues.filter(i => i.severity === 'critical');
    const errorIssues = issues.filter(i => i.severity === 'error');

    if (health.overall === 'unhealthy' || criticalIssues.length > 0) {
      this.state = 'critical';
    } else if (health.overall === 'degraded' || errorIssues.length > 0) {
      this.state = 'degraded';
    } else if (health.overall === 'healthy') {
      this.state = 'running';
    }
  }

  /**
   * Log health check summary
   */
  private logSummary(health: SystemHealth, issues: DetectedIssue[]): void {
    console.log('\n   📊 Service Status:');
    for (const service of health.services) {
      const emoji = service.status === 'healthy' ? '✅' : service.status === 'degraded' ? '⚠️' : '❌';
      console.log(`      ${emoji} ${service.service}: ${service.status}`);
      if (service.latencyMs) {
        console.log(`         Latency: ${service.latencyMs}ms`);
      }
      if (service.error) {
        console.log(`         Error: ${service.error}`);
      }
    }

    if (issues.length > 0) {
      console.log('\n   🚨 Active Issues:');
      for (const issue of issues.slice(0, 5)) {
        console.log(`      [${issue.severity.toUpperCase()}] ${issue.rootCause}`);
      }
    }
  }

  /**
   * Get current Guardian status
   */
  async getStatus(): Promise<GuardianStatus> {
    const health = await healthMonitor.checkAllServices();
    const issues = logAnalyzer.getActiveIssues();

    return {
      state: this.state,
      lastCheck: this.lastCheck,
      systemHealth: health,
      activeIssues: issues,
      scalingMetrics: [],
      uptime: Date.now() - this.startTime.getTime(),
      railwayConnected: !!railwayClient.getProjectId(),
    };
  }

  /**
   * Generate status report
   */
  generateReport(): string {
    const uptimeMs = Date.now() - this.startTime.getTime();
    const uptimeHours = (uptimeMs / (1000 * 60 * 60)).toFixed(1);

    let report = `# INFRA GUARDIAN - Status Report\n\n`;
    report += `**Generated:** ${new Date().toISOString()}\n`;
    report += `**State:** ${this.state.toUpperCase()}\n`;
    report += `**Uptime:** ${uptimeHours} hours\n\n`;

    report += `## System Health\n\n`;
    report += logAnalyzer.generateIssueSummary();

    report += `\n## Scaling\n\n`;
    report += autoScaler.getScalingSummary();

    report += `\n## Recent Alerts\n\n`;
    const recentAlerts = alertManager.getRecentAlerts(5);
    if (recentAlerts.length > 0) {
      for (const alert of recentAlerts) {
        report += `- [${alert.level.toUpperCase()}] ${alert.title}: ${alert.message}\n`;
      }
    } else {
      report += 'No recent alerts.\n';
    }

    return report;
  }

  /**
   * Get Railway services with status
   */
  async getRailwayServices(): Promise<Array<{ service: unknown; deployment: unknown }>> {
    return railwayClient.getAllServicesWithStatus();
  }

  /**
   * Trigger Railway deployment
   */
  async triggerDeployment(serviceId: string): Promise<void> {
    const deployment = await railwayClient.deployService(serviceId);
    console.log(`Triggered deployment for ${serviceId}:`, deployment);
    
    await alertManager.sendAlert(
      'info',
      'Deployment Triggered',
      `New deployment started for service ${serviceId}`
    );
  }
}

// Export singleton instance
export const guardian = new GuardianOrchestrator();
export default GuardianOrchestrator;

// CLI interface for running Guardian
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args[0] === 'start') {
    // Optional: Initialize with Railway token and alert config
    const railwayToken = process.env.RAILWAY_TOKEN;
    const railwayProjectId = process.env.RAILWAY_PROJECT_ID;
    
    const alertConfig: AlertConfig | undefined = process.env.SLACK_WEBHOOK_URL ? {
      slack: {
        webhookUrl: process.env.SLACK_WEBHOOK_URL,
        channel: process.env.SLACK_CHANNEL || '#alerts',
      },
    } : undefined;

    guardian.initialize(alertConfig, railwayToken, railwayProjectId)
      .then(() => guardian.start())
      .catch(console.error);
  } else if (args[0] === 'status') {
    guardian.runHealthCheck().then(status => {
      console.log('\n' + guardian.generateReport());
      process.exit(0);
    });
  } else {
    console.log('Usage:');
    console.log('  npx ts-node infra/guardian/index.ts start   # Start monitoring');
    console.log('  npx ts-node infra/guardian/index.ts status  # Get status report');
    console.log('\nEnvironment variables:');
    console.log('  RAILWAY_TOKEN          # Railway API token');
    console.log('  RAILWAY_PROJECT_ID     # Railway project ID');
    console.log('  SLACK_WEBHOOK_URL      # Slack webhook URL');
    console.log('  SLACK_CHANNEL          # Slack channel (default: #alerts)');
  }
}
