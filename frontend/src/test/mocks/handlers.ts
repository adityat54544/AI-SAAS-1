import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // Auth handlers - Backend as single source of truth
  http.get(`${API_URL}/auth/me`, () => {
    return HttpResponse.json({
      id: 'test-user-id',
      email: 'test@example.com',
      display_name: 'Test User',
      avatar_url: null,
      role: 'user',
    })
  }),

  http.get(`${API_URL}/auth/status`, () => {
    return HttpResponse.json({
      authenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
      },
    })
  }),

  http.post(`${API_URL}/auth/signout`, () => {
    return HttpResponse.json({ status: 'signed_out' })
  }),

  // Repositories handlers
  http.get(`${API_URL}/repositories`, () => {
    return HttpResponse.json({
      repositories: [
        {
          id: 'test-repo-id',
          name: 'test-repo',
          full_name: 'owner/test-repo',
          private: false,
          html_url: 'https://github.com/owner/test-repo',
          connected: true,
        },
      ],
    })
  }),

  // Analysis handlers
  http.post(`${API_URL}/analysis`, () => {
    return HttpResponse.json({
      id: 'test-analysis-id',
      status: 'pending',
      created_at: new Date().toISOString(),
    })
  }),

  http.get(`${API_URL}/analysis/:id`, () => {
    return HttpResponse.json({
      id: 'test-analysis-id',
      status: 'completed',
      results: {
        suggestions: [],
        issues: [],
      },
    })
  }),

  // Jobs handlers
  http.get(`${API_URL}/jobs`, () => {
    return HttpResponse.json({
      jobs: [
        {
          id: 'test-job-id',
          type: 'analysis',
          status: 'completed',
          created_at: new Date().toISOString(),
        },
      ],
    })
  }),

  // Health check
  http.get(`${API_URL}/health`, () => {
    return HttpResponse.json({ status: 'healthy' })
  }),
]
