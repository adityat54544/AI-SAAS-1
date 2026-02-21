import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // Auth handlers
  http.get(`${API_URL}/api/auth/user`, () => {
    return HttpResponse.json({
      id: 'test-user-id',
      email: 'test@example.com',
      name: 'Test User',
    })
  }),

  // Repositories handlers
  http.get(`${API_URL}/api/repositories`, () => {
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
  http.post(`${API_URL}/api/analysis`, () => {
    return HttpResponse.json({
      id: 'test-analysis-id',
      status: 'pending',
      created_at: new Date().toISOString(),
    })
  }),

  http.get(`${API_URL}/api/analysis/:id`, () => {
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
  http.get(`${API_URL}/api/jobs`, () => {
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