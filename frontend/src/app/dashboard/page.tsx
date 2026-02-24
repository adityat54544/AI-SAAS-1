'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Github, RefreshCw, BarChart3, Shield, Zap, GitBranch, LogOut, Settings, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { repositoriesApi, Repository } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton, StatsCardSkeleton } from '@/components/ui/skeleton';
import { StaggerContainer, StaggerItem } from '@/components/animated-layout';
import { ThemeToggle } from '@/components/theme-toggle';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full"
        />
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="max-w-md" hover animation="lift">
            <CardContent className="pt-8 pb-8 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
                className="w-20 h-20 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto mb-6"
              >
                <Sparkles className="w-10 h-10 text-primary-600 dark:text-primary-400" />
              </motion.div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Welcome to AutoDevOps AI</h2>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Connect your GitHub account to start analyzing and improving your repositories.
              </p>
              <Button size="lg" onClick={() => signIn()} className="gap-2">
                <Github className="w-5 h-5" />
                Connect with GitHub
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card hover animation="lift">
            <CardContent className="pt-8 pb-8 text-center">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Error Loading Dashboard</h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {error instanceof Error ? error.message : 'An error occurred while loading your data.'}
              </p>
              <Button onClick={() => refetch()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                <Sparkles className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AutoDevOps AI</h1>
                {user?.email && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => refetch()}
                className="hidden sm:flex"
              >
                <RefreshCw className="h-5 w-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                asChild
                className="hidden sm:flex"
              >
                <Link href="/settings">
                  <Settings className="h-5 w-5" />
                </Link>
              </Button>
              <Button
                variant="outline"
                onClick={() => signOut()}
                size="sm"
                className="gap-2"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign Out</span>
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StaggerItem>
            <Card hover animation="lift">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                    <GitBranch className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Repositories</p>
                    <p className="text-2xl font-bold">{repositories.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card hover animation="lift">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <Shield className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Security</p>
                    <p className="text-2xl font-bold">--</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card hover animation="lift">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                    <Zap className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Performance</p>
                    <p className="text-2xl font-bold">--</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card hover animation="lift">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <BarChart3 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Total Analyses</p>
                    <p className="text-2xl font-bold">--</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
        </StaggerContainer>

        {/* Repository List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Connected Repositories</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <StatsCardSkeleton key={i} />
                  ))}
                </div>
              ) : repositories.length === 0 ? (
                <div className="text-center py-12">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                    className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4"
                  >
                    <Github className="w-8 h-8 text-gray-400" />
                  </motion.div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No repositories connected</h3>
                  <p className="text-gray-500 dark:text-gray-400 mb-4">
                    Connect your GitHub repositories to start analyzing and improving your code.
                  </p>
                  <Button onClick={() => signIn()} className="gap-2">
                    <Github className="w-5 h-5" />
                    Connect GitHub
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {repositories.map((repo: Repository, index: number) => (
                    <motion.div
                      key={repo.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                    >
                      <Link href={`/repos/${repo.id}`}>
                        <Card hover animation="scale" className="cursor-pointer">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4">
                                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                  <GitBranch className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                                </div>
                                <div>
                                  <h3 className="font-medium text-gray-900 dark:text-white">
                                    {repo.full_name}
                                  </h3>
                                  <p className="text-sm text-gray-500 dark:text-gray-400">
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
                                <div className="text-right text-sm text-gray-500 dark:text-gray-400">
                                  {repo.last_analyzed_at ? (
                                    <span>Last analyzed: {new Date(repo.last_analyzed_at).toLocaleDateString()}</span>
                                  ) : (
                                    <span>Not yet analyzed</span>
                                  )}
                                </div>
                                <Button variant="ghost" size="sm">
                                  View
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </Link>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
