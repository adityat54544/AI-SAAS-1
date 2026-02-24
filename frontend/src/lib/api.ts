/**
 * API client for making authenticated requests to the backend.
 * Uses HttpOnly cookie-based authentication via credentials: "include".
 * 
 * Authentication flow:
 * 1. Frontend calls /auth/github to initiate OAuth (redirects to backend)
 * 2. Backend handles OAuth callback and sets HttpOnly session cookie
 * 3. Frontend calls /auth/me to validate session and get user info
 * 4. All API calls use credentials: "include" to send cookies
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

/**
 * Make an authenticated API request
 * Uses credentials: "include" to send HttpOnly cookies with cross-origin requests
 * @param endpoint - API endpoint (without base URL)
 * @param options - Fetch options
 * @returns Response data
 */
async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // NOTE: No Authorization header needed - using HttpOnly cookie-based auth
  // Cookie is automatically sent with credentials: "include"

  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
    mode: 'cors',
    credentials: 'include', // Critical: sends HttpOnly cookies with cross-origin requests
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'An error occurred',
    }));
    throw new APIError(response.status, error.detail || 'Request failed', error);
  }

  // Handle empty responses
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }

  return {} as T;
}

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

/**
 * API client methods
 */
export const api = {
  get: <T = unknown>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T = unknown>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};

/**
 * Authentication API endpoints
 * Uses backend as single source of truth for user identity
 */
export interface AuthUser {
  id: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
  role: string | null;
}

export const authApi = {
  /**
   * Get current authenticated user from backend
   * This is the single source of truth for frontend identity
   */
  me: () => api.get<AuthUser>('/auth/me'),
  
  /**
   * Check authentication status
   */
  status: () => api.get<{ authenticated: boolean; user?: { id: string; email: string } }>('/auth/status'),
  
  /**
   * Sign out - clears session cookie
   */
  signout: () => api.post<{ status: string }>('/auth/signout'),
  
  /**
   * Initiate GitHub OAuth - redirects to backend
   * Frontend should redirect to this URL, not fetch it
   */
  getGitHubAuthUrl: () => `${API_URL}/auth/github`,
};

/**
 * Repository API endpoints
 */
export const repositoriesApi = {
  list: () => api.get<{ repositories: Repository[] }>('/repositories'),
  
  get: (id: string) => api.get<Repository>(`/repositories/${id}`),
  
  connect: (installationId: string) =>
    api.post<Repository>('/repositories/connect', { installation_id: installationId }),
  
  sync: (id: string) =>
    api.post<{ status: string; job_id: string }>(`/repositories/${id}/sync`),
  
  disconnect: (id: string) =>
    api.delete<{ status: string }>(`/repositories/${id}`),
};

/**
 * Analysis API endpoints
 */
export const analysisApi = {
  create: (repositoryId: string, analysisType = 'full') =>
    api.post<{ status: string; analysis: Analysis; job_id: string }>('/analysis', {
      repository_id: repositoryId,
      analysis_type: analysisType,
    }),

  get: (analysisId: string) =>
    api.get<{ analysis: Analysis }>(`/analysis/${analysisId}`),

  list: (repositoryId: string, limit = 10, offset = 0) =>
    api.get<{ analyses: Analysis[] }>(
      `/analysis/repository/${repositoryId}?limit=${limit}&offset=${offset}`
    ),

  getRecommendations: (analysisId: string, category?: string, severity?: string) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (severity) params.append('severity', severity);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get<{ recommendations: Recommendation[] }>(
      `/analysis/${analysisId}/recommendations${query}`
    );
  },

  getRemediations: (analysisId: string) =>
    api.get<{ remediations: Remediation[] }>(`/analysis/${analysisId}/remediations`),

  applyRemediation: (analysisId: string, remediationId: string) =>
    api.post<{ status: string; remediation: Remediation }>(
      `/analysis/${analysisId}/apply?remediation_id=${remediationId}`
    ),
};

/**
 * Jobs API endpoints
 */
export const jobsApi = {
  get: (jobId: string) =>
    api.get<{ job: Job }>(`/jobs/${jobId}`),

  list: (limit = 10, offset = 0) =>
    api.get<{ jobs: Job[] }>(`/jobs?limit=${limit}&offset=${offset}`),

  getLogs: (jobId: string) =>
    api.get<{ logs: JobLog[] }>(`/jobs/${jobId}/logs`),
};

/**
 * CI/CD API endpoints
 */
export const ciCdApi = {
  generate: (repositoryId: string, template = 'default') =>
    api.post<{ status: string; config: CIConfig; pr_url?: string }>('/ci-cd/generate', {
      repository_id: repositoryId,
      template,
    }),

  preview: (repositoryId: string, template = 'default') =>
    api.post<{ config: string }>(`/ci-cd/preview`, {
      repository_id: repositoryId,
      template,
    }),
};

// Type definitions
export interface Repository {
  id: string;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  html_url: string;
  stargazers_count: number;
  forks_count: number;
  is_private: boolean;
  last_analyzed_at: string | null;
}

export interface Analysis {
  id: string;
  repository_id: string;
  status: string;
  analysis_type: string;
  triggered_by: string;
  created_at: string;
  completed_at?: string;
  results?: Record<string, unknown>;
}

export interface Recommendation {
  id: string;
  analysis_id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  suggested_fix?: string;
  file_path?: string;
  line_number?: number;
  created_at: string;
}

export interface Remediation {
  id: string;
  analysis_id: string;
  file_path: string;
  original_code: string;
  suggested_code: string;
  description: string;
  apply_status: string;
  created_at: string;
}

export interface Job {
  id: string;
  job_type: string;
  status: string;
  repository_id: string;
  payload: Record<string, unknown>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface JobLog {
  id: string;
  job_id: string;
  level: string;
  message: string;
  timestamp: string;
}

export interface CIConfig {
  id: string;
  repository_id: string;
  template: string;
  content: string;
  created_at: string;
}
