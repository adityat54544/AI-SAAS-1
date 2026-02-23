/**
 * INFRA GUARDIAN - Railway API Client
 * 
 * Integration with Railway API for live service discovery and management
 */

export interface RailwayProject {
  id: string;
  name: string;
  createdAt: string;
}

export interface RailwayService {
  id: string;
  name: string;
  createdAt: string;
  currentDeploymentId?: string;
}

export interface RailwayDeployment {
  id: string;
  status: 'BUILDING' | 'CREATED' | 'DEPLOYING' | 'ERROR' | 'READY' | 'REMOVED';
  createdAt: string;
  finishedAt?: string;
}

export interface RailwayServiceMetrics {
  serviceId: string;
  serviceName: string;
  cpu: number;
  memory: number;
  requests: number;
  avgLatency: number;
  errorRate: number;
}

export interface RailwayAutoscaling {
  enabled: boolean;
  minReplicas?: number;
  maxReplicas?: number;
  scaleUpThreshold?: number;
  scaleDownThreshold?: number;
}

class RailwayClient {
  private baseUrl = 'https://backboard.railway.app/v2';
  private projectId: string | null = null;
  private token: string | null = null;

  /**
   * Initialize with Railway API token and project ID
   */
  initialize(token: string, projectId?: string): void {
    this.token = token;
    if (projectId) {
      this.projectId = projectId;
    }
  }

  /**
   * Make authenticated request to Railway API
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    if (!this.token) {
      throw new Error('Railway API token not configured');
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Railway API error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  /**
   * Get project by name
   */
  async getProjectByName(projectName: string): Promise<RailwayProject | null> {
    const response = await this.request<{ projects: RailwayProject[] }>(
      `/projects/list`
    );

    const project = response.projects.find(
      (p) => p.name.toLowerCase() === projectName.toLowerCase()
    );

    if (project) {
      this.projectId = project.id;
    }

    return project || null;
  }

  /**
   * Get all services in the project
   */
  async getServices(): Promise<RailwayService[]> {
    if (!this.projectId) {
      throw new Error('Project ID not set. Call getProjectByName first.');
    }

    const response = await this.request<{ services: RailwayService[] }>(
      `/projects/${this.projectId}/services`
    );

    return response.services;
  }

  /**
   * Get a specific service by name
   */
  async getServiceByName(serviceName: string): Promise<RailwayService | null> {
    const services = await this.getServices();
    return (
      services.find(
        (s) => s.name.toLowerCase() === serviceName.toLowerCase()
      ) || null
    );
  }

  /**
   * Get current deployment status for a service
   */
  async getDeploymentStatus(serviceId: string): Promise<RailwayDeployment | null> {
    try {
      const response = await this.request<{ deployments: RailwayDeployment[] }>(
        `/deployments/list?serviceId=${serviceId}`
      );

      const latest = response.deployments[0];
      return latest || null;
    } catch {
      return null;
    }
  }

  /**
   * Get service metrics (requires Railway Plus)
   * Note: This is a placeholder - actual metrics require Railway's metrics API
   */
  async getServiceMetrics(serviceId: string): Promise<RailwayServiceMetrics | null> {
    // Railway's metrics API is available on paid plans
    // This is a simplified implementation that returns estimated metrics
    try {
      const service = await this.getServiceById(serviceId);
      if (!service) return null;

      return {
        serviceId,
        serviceName: service.name,
        cpu: 0, // Would come from Railway metrics API
        memory: 0,
        requests: 0,
        avgLatency: 0,
        errorRate: 0,
      };
    } catch {
      return null;
    }
  }

  /**
   * Get service by ID
   */
  async getServiceById(serviceId: string): Promise<RailwayService | null> {
    try {
      return await this.request<RailwayService>(`/services/${serviceId}`);
    } catch {
      return null;
    }
  }

  /**
   * Get environment variables for a service
   */
  async getServiceVariables(serviceId: string): Promise<Record<string, string>> {
    const response = await this.request<{ variables: Array<{ key: string; value: string }> }>(
      `/services/${serviceId}/variables`
    );

    const variables: Record<string, string> = {};
    for (const { key, value } of response.variables) {
      variables[key] = value;
    }

    return variables;
  }

  /**
   * Update environment variables for a service (e.g., for scaling)
   */
  async updateServiceVariables(
    serviceId: string,
    variables: Record<string, string>
  ): Promise<void> {
    await this.request(`/services/${serviceId}/variables`, {
      method: 'PATCH',
      body: JSON.stringify({ variables }),
    });
  }

  /**
   * Get autoscaling configuration for a service
   */
  async getAutoscalingConfig(serviceId: string): Promise<RailwayAutoscaling | null> {
    try {
      const response = await this.request<{ autoscaling: RailwayAutoscaling }>(
        `/services/${serviceId}/autoscaling`
      );
      return response.autoscaling;
    } catch {
      return null;
    }
  }

  /**
   * Configure autoscaling for a service
   */
  async setAutoscalingConfig(
    serviceId: string,
    config: RailwayAutoscaling
  ): Promise<void> {
    await this.request(`/services/${serviceId}/autoscaling`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  /**
   * Trigger a new deployment
   */
  async deployService(serviceId: string): Promise<RailwayDeployment> {
    return this.request<RailwayDeployment>(`/deployments`, {
      method: 'POST',
      body: JSON.stringify({ serviceId }),
    });
  }

  /**
   * Get project environments
   */
  async getEnvironments(): Promise<Array<{ id: string; name: string }>> {
    if (!this.projectId) {
      throw new Error('Project ID not set');
    }

    const response = await this.request<{ environments: Array<{ id: string; name: string }> }>(
      `/projects/${this.projectId}/environments`
    );

    return response.environments;
  }

  /**
   * Get service logs
   */
  async getServiceLogs(
    serviceId: string,
    limit: number = 100
  ): Promise<string[]> {
    const response = await this.request<{ logs: string[] }>(
      `/logs?serviceId=${serviceId}&limit=${limit}`
    );

    return response.logs;
  }

  /**
   * Check if Railway API is configured and accessible
   */
  async checkConnection(): Promise<boolean> {
    try {
      await this.request<{ projects: RailwayProject[] }>('/projects/list');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get project ID
   */
  getProjectId(): string | null {
    return this.projectId;
  }

  /**
   * Get all services with their deployment status
   */
  async getAllServicesWithStatus(): Promise<
    Array<{
      service: RailwayService;
      deployment: RailwayDeployment | null;
      metrics: RailwayServiceMetrics | null;
    }>
  > {
    const services = await this.getServices();
    const result = [];

    for (const service of services) {
      const deployment = await this.getDeploymentStatus(service.id);
      const metrics = await this.getServiceMetrics(service.id);

      result.push({ service, deployment, metrics });
    }

    return result;
  }
}

export const railwayClient = new RailwayClient();
export default RailwayClient;
