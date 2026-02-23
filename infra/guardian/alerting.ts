/**
 * INFRA GUARDIAN - Alerting System
 * 
 * Multi-channel alerting for Slack, Discord, PagerDuty
 */

import { guardianConfig } from './config';
import type { ServiceHealth, SystemHealth } from './health-monitor';
import type { ScalingDecision } from './auto-scaler';

export type AlertLevel = 'info' | 'warning' | 'critical';
export type AlertChannel = 'slack' | 'discord' | 'pagerduty' | 'email';

export interface Alert {
  id: string;
  level: AlertLevel;
  title: string;
  message: string;
  channel: AlertChannel;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

export interface AlertConfig {
  slack?: {
    webhookUrl: string;
    channel: string;
    username?: string;
  };
  discord?: {
    webhookUrl: string;
    username?: string;
    avatarUrl?: string;
  };
  pagerduty?: {
    apiKey: string;
    serviceId: string;
    integrationKey: string;
  };
  email?: {
    smtpHost: string;
    smtpPort: number;
    username: string;
    password: string;
    from: string;
    to: string[];
  };
}

// Store recent alerts to avoid spam
class AlertManager {
  private recentAlerts: Map<string, Alert> = new Map();
  private config: AlertConfig | null = null;
  private alertCooldownMs = 5 * 60 * 1000; // 5 minutes between similar alerts

  /**
   * Initialize with alert configuration
   */
  configure(config: AlertConfig): void {
    this.config = config;
  }

  /**
   * Generate unique key for alert deduplication
   */
  private getAlertKey(level: AlertLevel, title: string, channel: AlertChannel): string {
    return `${channel}:${level}:${title}`;
  }

  /**
   * Check if alert should be sent (rate limiting)
   */
  private shouldSendAlert(level: AlertLevel, title: string, channel: AlertChannel): boolean {
    const key = this.getAlertKey(level, title, channel);
    const lastAlert = this.recentAlerts.get(key);

    if (!lastAlert) {
      return true;
    }

    const timeSinceLastAlert = Date.now() - lastAlert.timestamp.getTime();
    return timeSinceLastAlert >= this.alertCooldownMs;
  }

  /**
   * Record alert sent
   */
  private recordAlert(alert: Alert): void {
    const key = this.getAlertKey(alert.level, alert.title, alert.channel);
    this.recentAlerts.set(key, alert);

    // Clean up old alerts
    if (this.recentAlerts.size > 100) {
      const oldestKey = this.recentAlerts.keys().next().value;
      if (oldestKey) {
        this.recentAlerts.delete(oldestKey);
      }
    }
  }

  /**
   * Send alert to Slack
   */
  async sendSlackAlert(level: AlertLevel, title: string, message: string): Promise<boolean> {
    if (!this.config?.slack) {
      console.warn('Slack not configured');
      return false;
    }

    if (!this.shouldSendAlert(level, title, 'slack')) {
      console.log(`Slack alert rate-limited: ${title}`);
      return false;
    }

    const { webhookUrl, channel, username = 'Infra Guardian' } = this.config.slack;

    const emoji = level === 'critical' ? '🔴' : level === 'warning' ? '🟡' : '🔵';

    const payload = {
      channel,
      username,
      attachments: [
        {
          color: level === 'critical' ? '#ff0000' : level === 'warning' ? '#ffa500' : '#0088ff',
          title: `${emoji} ${title}`,
          text: message,
          footer: 'INFRA GUARDIAN',
          ts: Math.floor(Date.now() / 1000),
        },
      ],
    };

    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const alert: Alert = {
          id: `slack-${Date.now()}`,
          level,
          title,
          message,
          channel: 'slack',
          timestamp: new Date(),
        };
        this.recordAlert(alert);
        return true;
      }

      console.error('Slack alert failed:', await response.text());
      return false;
    } catch (error) {
      console.error('Failed to send Slack alert:', error);
      return false;
    }
  }

  /**
   * Send alert to Discord
   */
  async sendDiscordAlert(level: AlertLevel, title: string, message: string): Promise<boolean> {
    if (!this.config?.discord) {
      console.warn('Discord not configured');
      return false;
    }

    if (!this.shouldSendAlert(level, title, 'discord')) {
      console.log(`Discord alert rate-limited: ${title}`);
      return false;
    }

    const { webhookUrl, username = 'Infra Guardian', avatarUrl } = this.config.discord;

    const color = level === 'critical' ? 16711680 : level === 'warning' ? 16744448 : 3447003;

    const payload = {
      username,
      avatar_url: avatarUrl,
      embeds: [
        {
          title,
          description: message,
          color,
          timestamp: new Date().toISOString(),
          footer: { text: 'INFRA GUARDIAN' },
        },
      ],
    };

    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const alert: Alert = {
          id: `discord-${Date.now()}`,
          level,
          title,
          message,
          channel: 'discord',
          timestamp: new Date(),
        };
        this.recordAlert(alert);
        return true;
      }

      console.error('Discord alert failed:', await response.text());
      return false;
    } catch (error) {
      console.error('Failed to send Discord alert:', error);
      return false;
    }
  }

  /**
   * Send alert to PagerDuty
   */
  async sendPagerDutyAlert(
    level: AlertLevel,
    title: string,
    message: string,
    metadata?: Record<string, unknown>
  ): Promise<boolean> {
    if (!this.config?.pagerduty) {
      console.warn('PagerDuty not configured');
      return false;
    }

    if (!this.shouldSendAlert(level, title, 'pagerduty')) {
      console.log(`PagerDuty alert rate-limited: ${title}`);
      return false;
    }

    const { apiKey, serviceId, integrationKey } = this.config.pagerduty;

    const urgency = level === 'critical' ? 'high' : 'low';

    const payload = {
      routing_key: integrationKey,
      event_action: 'trigger',
      payload: {
        summary: title,
        severity: level === 'critical' ? 'critical' : level === 'warning' ? 'warning' : 'info',
        source: 'infra-guardian',
        custom_details: {
          message,
          ...metadata,
        },
      },
      client: 'INFRA GUARDIAN',
      client_url: process.env.GUARDIAN_DASHBOARD_URL || 'https://dashboard.example.com',
    };

    try {
      const response = await fetch(
        `https://events.pagerduty.com/v2/enqueue`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Token token=${apiKey}`,
          },
          body: JSON.stringify(payload),
        }
      );

      if (response.ok) {
        const alert: Alert = {
          id: `pagerduty-${Date.now()}`,
          level,
          title,
          message,
          channel: 'pagerduty',
          timestamp: new Date(),
          metadata,
        };
        this.recordAlert(alert);
        return true;
      }

      console.error('PagerDuty alert failed:', await response.text());
      return false;
    } catch (error) {
      console.error('Failed to send PagerDuty alert:', error);
      return false;
    }
  }

  /**
   * Resolve PagerDuty alert
   */
  async resolvePagerDutyAlert(alertId: string): Promise<boolean> {
    if (!this.config?.pagerduty) {
      return false;
    }

    const { apiKey, integrationKey } = this.config.pagerduty;

    const payload = {
      routing_key: integrationKey,
      event_action: 'resolve',
      dedup_key: alertId,
    };

    try {
      const response = await fetch('https://events.pagerduty.com/v2/enqueue', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Token token=${apiKey}`,
        },
        body: JSON.stringify(payload),
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to resolve PagerDuty alert:', error);
      return false;
    }
  }

  /**
   * Send email alert
   */
  async sendEmailAlert(level: AlertLevel, title: string, message: string): Promise<boolean> {
    // Note: In production, use a proper email library like nodemailer
    console.warn('Email alerting requires nodemailer setup');
    return false;
  }

  /**
   * Send alert to all configured channels
   */
  async sendAlert(
    level: AlertLevel,
    title: string,
    message: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    const promises: Promise<boolean>[] = [];

    if (this.config?.slack) {
      promises.push(this.sendSlackAlert(level, title, message));
    }

    if (this.config?.discord) {
      promises.push(this.sendDiscordAlert(level, title, message));
    }

    if (this.config?.pagerduty && level !== 'info') {
      // Only send to PagerDuty for warnings and critical
      promises.push(this.sendPagerDutyAlert(level, title, message, metadata));
    }

    if (this.config?.email) {
      promises.push(this.sendEmailAlert(level, title, message));
    }

    await Promise.allSettled(promises);
  }

  /**
   * Send service health alert
   */
  async alertServiceHealth(health: ServiceHealth): Promise<void> {
    const { status, service, error, latencyMs } = health;

    if (status === 'healthy') return;

    const level: AlertLevel = status === 'unhealthy' ? 'critical' : 'warning';
    const title = `Service ${status}: ${service}`;
    const message = error
      ? `Service ${service} is ${status}. Error: ${error}${latencyMs ? ` (${latencyMs}ms)` : ''}`
      : `Service ${service} is ${status}${latencyMs ? ` (${latencyMs}ms)` : ''}`;

    await this.sendAlert(level, title, message, { service, status, error, latencyMs });
  }

  /**
   * Send scaling alert
   */
  async alertScaling(decision: ScalingDecision): Promise<void> {
    if (decision.action === 'maintain') return;

    const level: AlertLevel = decision.action === 'scale_up' ? 'warning' : 'info';
    const title = `Auto-scale ${decision.service}: ${decision.action}`;
    const message = `Scaling ${decision.service} from ${decision.currentReplicas} to ${decision.recommendedReplicas}. Reason: ${decision.reason}`;

    await this.sendAlert(level, title, message, {
      service: decision.service,
      action: decision.action,
      currentReplicas: decision.currentReplicas,
      recommendedReplicas: decision.recommendedReplicas,
    });
  }

  /**
   * Send system health summary
   */
  async alertSystemHealth(health: SystemHealth): Promise<void> {
    if (health.overall === 'healthy') return;

    const level: AlertLevel = health.overall === 'unhealthy' ? 'critical' : 'warning';
    const title = `System ${health.overall}`;
    const services = health.services
      .map(s => `${s.service}: ${s.status}`)
      .join(', ');

    await this.sendAlert(
      level,
      title,
      `System is ${health.overall}. Services: ${services}`,
      { services: health.services }
    );
  }

  /**
   * Get recent alerts
   */
  getRecentAlerts(limit: number = 10): Alert[] {
    return Array.from(this.recentAlerts.values())
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }

  /**
   * Clear alert history
   */
  clearAlerts(): void {
    this.recentAlerts.clear();
  }
}

export const alertManager = new AlertManager();
export default AlertManager;
