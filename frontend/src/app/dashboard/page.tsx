'use client';

import { useQuery } from '@tanstack/react-query';
import { GitHub, RefreshCw, BarChart3, Shield, Zap, GitBranch } from 'lucide-react';
import Link from 'next/link';

interface Repository {
  id: string;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  html_url: string;
  stargazers_count: number;
  is_private: boolean;
  last_analyzed_at: string | null;
}

async function fetchRepositories() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/repositories`, {
    credentials: 'include',
  });
  if (!response.ok) throw new Error('Failed to fetch repositories');
  return response.json();
}

export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  });

  const repositories = data?.repositories || [];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">Please connect your GitHub account to continue.</p>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/github`}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <GitHub className="w-5 h-5" />
            Connect GitHub
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">AutoDevOps AI</h1>
            <div className="flex items-center gap-4">
              <button
                onClick={() => refetch()}
                className="btn btn-secondary inline-flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/github`}
                className="btn btn-primary inline-flex items-center gap-2"
              >
                <GitHub className="w-5 h-5" />
                Connect Repository
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-primary-100 text-primary-600">
                <GitBranch className="w-6 h-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Repositories</p>
                <p className="text-2xl font-semibold text-gray-900">{repositories.length}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                <Shield className="w-6 h-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Security</p>
                <p className="text-2xl font-semibold text-gray-900">--</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                <Zap className="w-6 h-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Performance</p>
                <p className="text-2xl font-semibold text-gray-900">--</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                <BarChart3 className="w-6 h-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Analyses</p>
                <p className="text-2xl font-semibold text-gray-900">--</p>
              </div>
            </div>
          </div>
        </div>

        {/* Repository List */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Connected Repositories</h2>
          
          {repositories.length === 0 ? (
            <div className="text-center py-12">
              <GitHub className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No repositories connected</h3>
              <p className="text-gray-500 mb-4">
                Connect your GitHub repositories to start analyzing and improving your code.
              </p>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/github`}
                className="btn btn-primary inline-flex items-center gap-2"
              >
                <GitHub className="w-5 h-5" />
                Connect GitHub
              </a>
            </div>
          ) : (
            <div className="space-y-4">
              {repositories.map((repo: Repository) => (
                <div
                  key={repo.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <GitBranch className="w-5 h-5 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">
                        <a href={`/repositories/${repo.id}`} className="hover:text-primary-600">
                          {repo.full_name}
                        </a>
                      </h3>
                      <p className="text-sm text-gray-500">
                        {repo.description || 'No description'}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {repo.language && (
                          <span className="badge badge-info">{repo.language}</span>
                        )}
                        {repo.is_private ? (
                          <span className="badge badge-warning">Private</span>
                        ) : (
                          <span className="badge badge-success">Public</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right text-sm text-gray-500">
                      {repo.last_analyzed_at ? (
                        <span>Last analyzed: {new Date(repo.last_analyzed_at).toLocaleDateString()}</span>
                      ) : (
                        <span>Not yet analyzed</span>
                      )}
                    </div>
                    <Link
                      href={`/repositories/${repo.id}`}
                      className="btn btn-secondary text-sm"
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}