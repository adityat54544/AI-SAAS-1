/**
 * INFRA GUARDIAN Configuration
 * 
 * Autonomous SRE System Configuration
 */

export const guardianConfig = {
  // Health check configuration
  healthCheck: {
    intervalMs: 60000, // 60 seconds
    timeoutMs: 10000,
    retries: 3,
  },
  
  // Service endpoints
  services: {
    api: {
      name: 'autodevops-api',
      healthPath: '/health',
      readinessPath: '/ready',
      url: process.env.API_URL || 'https://ai-saas-1-production.up.railway.app',
    },
    frontend: {
      name: 'autodevops-frontend',
      healthPath: '/healthz',
      url: process.env.FRONTEND_URL || 'https://autodevops.ai',
    },
  },
  
  // Alert thresholds
  thresholds: {
    maxRestartCount: 3,
    maxLatencyMs: 2000,
    maxErrorRate: 0.05,
    maxQueueDepth: 100,
  },
  
  // Scaling configuration
  scaling: {
    workerMinReplicas: 1,
    workerMaxReplicas: 5,
    workerScaleUpThreshold: 50,
    workerScaleDownThreshold: 5,
    cooldownMinutes: 10,
    apiMinReplicas: 1,
    apiMaxReplicas: 3,
    apiScaleUpThreshold: 1000,
  },
  
  // Anomaly detection
  anomalyDetection: {
    baselineWindowMs: 3600000, // 1 hour
    deviationMultiplier: 2,
    minDataPoints: 10,
  },
  
  // Auto-patch settings
  autoPatch: {
    enabled: true,
    requireApproval: true,
    maxAutoRetries: 2,
  },
  
  // Monitoring
  monitoring: {
    logRetentionDays: 30,
    metricsRetentionDays: 90,
  },
};

export type GuardianConfig = typeof guardianConfig;
