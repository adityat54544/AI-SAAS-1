/**
 * INFRA GUARDIAN - Health Monitor
 * 
 * Continuous health monitoring for all services
 */

import { guardianConfig } from './config';

export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export interface ServiceHealth {
  service: string;
  status: ServiceStatus;
  lastChecked: Date;
  latencyMs?: number;
  error?: string;
  details?: Record<string, unknown>;
}

export interface SystemHealth {
  overall: ServiceStatus;
  services: ServiceHealth[];
  timestamp: Date;
}

class HealthMonitor {
  private healthHistory: Map<string, ServiceHealth[]> = new Map();
  private readonly maxHistorySize = 100;

  /**
   * Check health of a single service
   */
  async checkServiceHealth(
    name: string,
    url: string,
    path: string
  ): Promise<ServiceHealth> {
    const startTime = Date.now();
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), guardianConfig.healthCheck.timeoutMs);

      const response = await fetch(`${url}${path}`, {
        method: 'HEAD',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      const latencyMs = Date.now() - startTime;
      
      if (response.ok) {
        return {
          service: name,
          status: 'healthy',
          lastChecked: new Date(),
          latencyMs,
        };
      } else if (response.status >= 500) {
        return {
          service: name,
          status: 'unhealthy',
          lastChecked: new Date(),
          latencyMs,
          error: `HTTP ${response.status}`,
        };
      } else {
        return {
          service: name,
          status: 'degraded',
          lastChecked: new Date(),
          latencyMs,
          error: `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      const latencyMs = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      return {
        service: name,
        status: 'unhealthy',
        lastChecked: new Date(),
        latencyMs,
        error: errorMessage,
      };
    }
  }

  /**
   * Check API readiness (includes DB check)
   */
  async checkApiReadiness(): Promise<ServiceHealth> {
    const { api } = guardianConfig.services;
    
    try {
      const response = await fetch(`${api.url}${api.readinessPath}`, {
        method: 'GET',
      });
      
      const data = await response.json();
      
      return {
        service: `${api.name}-readiness`,
        status: data.ready ? 'healthy' : 'degraded',
        lastChecked: new Date(),
        details: data.checks,
      };
    } catch (error) {
      return {
        service: `${api.name}-readiness`,
        status: 'unhealthy',
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Check all services
   */
  async checkAllServices(): Promise<SystemHealth> {
    const { api, frontend } = guardianConfig.services;
    
    const results: ServiceHealth[] = [];
    
    // Check API health
    const apiHealth = await this.checkServiceHealth(api.name, api.url, api.healthPath);
    results.push(apiHealth);
    
    // Check frontend health
    const frontendHealth = await this.checkServiceHealth(
      frontend.name, 
      frontend.url, 
      frontend.healthPath
    );
    results.push(frontendHealth);
    
    // Check API readiness
    const readinessHealth = await this.checkApiReadiness();
    results.push(readinessHealth);
    
    // Store in history
    for (const health of results) {
      this.addToHistory(health.service, health);
    }
    
    // Determine overall status
    const overall = this.calculateOverallStatus(results);
    
    return {
      overall,
      services: results,
      timestamp: new Date(),
    };
  }

  /**
   * Calculate overall system status
   */
  private calculateOverallStatus(services: ServiceHealth[]): ServiceStatus {
    const statuses = services.map(s => s.status);
    
    if (statuses.every(s => s === 'healthy')) {
      return 'healthy';
    }
    
    if (statuses.some(s => s === 'unhealthy')) {
      return 'unhealthy';
    }
    
    if (statuses.some(s => s === 'degraded')) {
      return 'degraded';
    }
    
    return 'unknown';
  }

  /**
   * Add health result to history
   */
  private addToHistory(service: string, health: ServiceHealth): void {
    const history = this.healthHistory.get(service) || [];
    history.push(health);
    
    if (history.length > this.maxHistorySize) {
      history.shift();
    }
    
    this.healthHistory.set(service, history);
  }

  /**
   * Get health history for a service
   */
  getHealthHistory(service: string): ServiceHealth[] {
    return this.healthHistory.get(service) || [];
  }

  /**
   * Get recent error rate for a service
   */
  getErrorRate(service: string): number {
    const history = this.getHealthHistory(service);
    
    if (history.length === 0) {
      return 0;
    }
    
    const errorCount = history.filter(h => h.status === 'unhealthy').length;
    return errorCount / history.length;
  }

  /**
   * Get average latency for a service
   */
  getAverageLatency(service: string): number {
    const history = this.getHealthHistory(service);
    
    if (history.length === 0) {
      return 0;
    }
    
    const withLatency = history.filter(h => h.latencyMs !== undefined);
    
    if (withLatency.length === 0) {
      return 0;
    }
    
    const total = withLatency.reduce((sum, h) => sum + (h.latencyMs || 0), 0);
    return total / withLatency.length;
  }
}

export const healthMonitor = new HealthMonitor();
export default HealthMonitor;
