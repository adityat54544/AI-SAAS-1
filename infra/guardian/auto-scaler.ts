/**
 * INFRA GUARDIAN - Auto-Scaler
 * 
 * Self-healing dynamic scaling for workers and API
 */

import { guardianConfig } from './config';
import { healthMonitor, SystemHealth } from './health-monitor';

export type ScalingAction = 'scale_up' | 'scale_down' | 'maintain';
export type ServiceType = 'workers' | 'api';

export interface ScalingDecision {
  action: ScalingAction;
  service: ServiceType;
  currentReplicas: number;
  recommendedReplicas: number;
  reason: string;
  timestamp: Date;
}

export interface ScalingMetrics {
  service: ServiceType;
  currentReplicas: number;
  queueDepth?: number;
  latencyMs?: number;
  errorRate?: number;
  recommendation: ScalingDecision;
}

class AutoScaler {
  private lastScalingAction: Map<ServiceType, Date> = new Map();
  private scalingHistory: ScalingDecision[] = [];

  /**
   * Check if scaling is allowed (cooldown period)
   */
  private isScalingAllowed(service: ServiceType): boolean {
    const lastAction = this.lastScalingAction.get(service);
    
    if (!lastAction) {
      return true;
    }
    
    const cooldownMs = guardianConfig.scaling.cooldownMinutes * 60 * 1000;
    const timeSinceLastAction = Date.now() - lastAction.getTime();
    
    return timeSinceLastAction >= cooldownMs;
  }

  /**
   * Calculate recommended worker replicas based on queue depth
   */
  calculateWorkerScaling(queueDepth: number, currentReplicas: number): ScalingDecision {
    const { 
      workerMinReplicas, 
      workerMaxReplicas,
      workerScaleUpThreshold,
      workerScaleDownThreshold,
    } = guardianConfig.scaling;
    
    // Check cooldown
    if (!this.isScalingAllowed('workers')) {
      return {
        action: 'maintain',
        service: 'workers',
        currentReplicas,
        recommendedReplicas: currentReplicas,
        reason: 'Cooldown period active',
        timestamp: new Date(),
      };
    }
    
    // Scale up decision
    if (queueDepth > workerScaleUpThreshold) {
      const recommended = Math.min(currentReplicas + 1, workerMaxReplicas);
      
      if (recommended > currentReplicas) {
        this.lastScalingAction.set('workers', new Date());
        
        return {
          action: 'scale_up',
          service: 'workers',
          currentReplicas,
          recommendedReplicas: recommended,
          reason: `Queue depth (${queueDepth}) exceeds threshold (${workerScaleUpThreshold})`,
          timestamp: new Date(),
        };
      }
    }
    
    // Scale down decision (only when queue is very low)
    if (queueDepth < workerScaleDownThreshold && currentReplicas > workerMinReplicas) {
      const recommended = Math.max(currentReplicas - 1, workerMinReplicas);
      
      this.lastScalingAction.set('workers', new Date());
      
      return {
        action: 'scale_down',
        service: 'workers',
        currentReplicas,
        recommendedReplicas: recommended,
        reason: `Queue depth (${queueDepth}) below threshold (${workerScaleDownThreshold})`,
        timestamp: new Date(),
      };
    }
    
    // Maintain current state
    return {
      action: 'maintain',
      service: 'workers',
      currentReplicas,
      recommendedReplicas: currentReplicas,
      reason: 'Queue depth within acceptable range',
      timestamp: new Date(),
    };
  }

  /**
   * Calculate recommended API replicas based on latency
   */
  async calculateApiScaling(currentReplicas: number): Promise<ScalingDecision> {
    const { 
      apiMinReplicas, 
      apiMaxReplicas,
      apiScaleUpThreshold,
    } = guardianConfig.scaling;
    
    // Check cooldown
    if (!this.isScalingAllowed('api')) {
      return {
        action: 'maintain',
        service: 'api',
        currentReplicas,
        recommendedReplicas: currentReplicas,
        reason: 'Cooldown period active',
        timestamp: new Date(),
      };
    }
    
    // Get health metrics
    const health = await healthMonitor.checkAllServices();
    const latency = healthMonitor.getAverageLatency('autodevops-api');
    const errorRate = healthMonitor.getErrorRate('autodevops-api');
    
    // Scale up if latency is high or error rate is high
    const maxLatency = guardianConfig.thresholds.maxLatencyMs;
    const maxErrorRate = guardianConfig.thresholds.maxErrorRate;
    
    if (latency > maxLatency || errorRate > maxErrorRate) {
      const recommended = Math.min(currentReplicas + 1, apiMaxReplicas);
      
      if (recommended > currentReplicas) {
        this.lastScalingAction.set('api', new Date());
        
        let reason = '';
        if (latency > maxLatency) {
          reason = `Latency (${latency}ms) exceeds threshold (${maxLatency}ms)`;
        } else {
          reason = `Error rate (${(errorRate * 100).toFixed(1)}%) exceeds threshold (${(maxErrorRate * 100).toFixed(1)}%)`;
        }
        
        return {
          action: 'scale_up',
          service: 'api',
          currentReplicas,
          recommendedReplicas: recommended,
          reason,
          timestamp: new Date(),
        };
      }
    }
    
    // Scale down if latency is very low and error rate is minimal
    if (latency < 100 && errorRate < 0.01 && currentReplicas > apiMinReplicas) {
      const recommended = Math.max(currentReplicas - 1, apiMinReplicas);
      
      this.lastScalingAction.set('api', new Date());
      
      return {
        action: 'scale_down',
        service: 'api',
        currentReplicas,
        recommendedReplicas: recommended,
        reason: `Latency (${latency}ms) and error rate (${(errorRate * 100).toFixed(1)}%) are minimal`,
        timestamp: new Date(),
      };
    }
    
    // Maintain current state
    return {
      action: 'maintain',
      service: 'api',
      currentReplicas,
      recommendedReplicas: currentReplicas,
      reason: 'Metrics within acceptable range',
      timestamp: new Date(),
    };
  }

  /**
   * Get scaling recommendation for all services
   */
  async getAllScalingRecommendations(
    workerQueueDepth: number,
    currentWorkerReplicas: number,
    currentApiReplicas: number
  ): Promise<ScalingMetrics[]> {
    const recommendations: ScalingMetrics[] = [];
    
    // Workers
    const workerDecision = this.calculateWorkerScaling(workerQueueDepth, currentWorkerReplicas);
    recommendations.push({
      service: 'workers',
      currentReplicas: currentWorkerReplicas,
      queueDepth: workerQueueDepth,
      recommendation: workerDecision,
    });
    
    // API
    const apiDecision = await this.calculateApiScaling(currentApiReplicas);
    const health = await healthMonitor.checkAllServices();
    const apiHealth = health.services.find(s => s.service === 'autodevops-api');
    
    recommendations.push({
      service: 'api',
      currentReplicas: currentApiReplicas,
      latencyMs: apiHealth?.latencyMs,
      errorRate: healthMonitor.getErrorRate('autodevops-api'),
      recommendation: apiDecision,
    });
    
    // Record in history
    this.scalingHistory.push(workerDecision, apiDecision);
    
    // Keep only recent history
    if (this.scalingHistory.length > 100) {
      this.scalingHistory.shift();
    }
    
    return recommendations;
  }

  /**
   * Get scaling history
   */
  getScalingHistory(): ScalingDecision[] {
    return [...this.scalingHistory];
  }

  /**
   * Get time until scaling is allowed
   */
  getTimeUntilScalingAllowed(service: ServiceType): number | null {
    const lastAction = this.lastScalingAction.get(service);
    
    if (!lastAction) {
      return 0;
    }
    
    const cooldownMs = guardianConfig.scaling.cooldownMinutes * 60 * 1000;
    const timeSinceLastAction = Date.now() - lastAction.getTime();
    const remaining = cooldownMs - timeSinceLastAction;
    
    return remaining > 0 ? remaining : 0;
  }

  /**
   * Force reset cooldown (for emergency situations)
   */
  resetCooldown(service: ServiceType): void {
    this.lastScalingAction.delete(service);
  }

  /**
   * Get scaling summary
   */
  getScalingSummary(): string {
    const recent = this.scalingHistory.slice(-10);
    
    let summary = '## Scaling Summary\n\n';
    summary += `Recent actions (last 10):\n`;
    
    for (const decision of recent.reverse()) {
      const emoji = decision.action === 'scale_up' ? '⬆️' : decision.action === 'scale_down' ? '⬇️' : '➡️';
      summary += `- ${emoji} ${decision.service}: ${decision.action} (${decision.currentReplicas} → ${decision.recommendedReplicas}) - ${decision.reason}\n`;
    }
    
    return summary;
  }
}

export const autoScaler = new AutoScaler();
export default AutoScaler;
