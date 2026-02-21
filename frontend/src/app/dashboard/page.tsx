'use client';

import { useQuery } from '@tanstack/react-query';
import { Github, RefreshCw, BarChart3, Shield, Zap, GitBranch, LogOut } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { repositoriesApi, Repository } from '@/lib/api';

export default function DashboardPage() {
  const { user, isLoading: authLoading, isAuthenticated, signIn, signOut } = useAuth();

  const { data, isLoading: reposLoading, error, refetch } = useQuery({
    queryKey: ['repositories'],
    queryFn: repositoriesApi.list,
    enabled: isAuthenticated,
  });

  const repositories = data?.repositories || [];
  const isLoading = authLoading || reposLoading;

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto p-8">
          <Github className="w-16 h-16 text-gray-400 mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to AutoDevOps AI</h2>
          <p className="text-gray-600 mb-6">
            Connect your GitHub account to start analyzing and improving your repositories.
          </p>
          <button
            onClick={() => signIn()}
            className="btn btn-primary inline-flex items-center gap-2 px-6 py-3"
          >
            <Github className="w-5 h-5" />
            Connect with GitHub
          </button>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">
            {error instanceof Error ? error.message : 'An error occurred while loading your data.'}
          </p>
          <button
            onClick={() => refetch()}
            className="btn btn-primary"
          >
            Try Again
          </button>
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
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-900">AutoDevOps AI</h1>
              {user?.email && (
                <span className="text-sm text-gray-500">{user.email}</span>
              )}
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => refetch()}
                className="btn btn-secondary inline-flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <button
                onClick={() => signIn()}
                className="btn btn-primary inline-flex items-center gap-2"
              >
                <Github className="w-5 h-5" />
                Connect Repository
              </button>
              <button
                onClick={signOut}
                className="btn btn-secondary inline-flex items-center gap-2"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
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
          
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : repositories.length === 0 ? (
            <div className="text-center py-12">
              <Github className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No repositories connected</h3>
              <p className="text-gray-500 mb-4">
                Connect your GitHub repositories to start analyzing and improving your code.
              </p>
              <button
                onClick={() => signIn()}
                className="btn btn-primary inline-flex items-center gap-2"
              >
                <Github className="w-5 h-5" />
                Connect GitHub
              </button>
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
                        <Link href={`/repositories/${repo.id}`} className="hover:text-primary-600">
                          {repo.full_name}
                        </Link>
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