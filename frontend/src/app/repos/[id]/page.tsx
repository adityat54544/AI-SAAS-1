'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  GitBranch, 
  Star, 
  GitFork, 
  Lock, 
  Globe, 
  Calendar,
  RefreshCw,
  Play,
  Settings,
  ExternalLink,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Clock
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { repositoriesApi, analysisApi, Repository, Analysis } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton, StatsCardSkeleton } from '@/components/ui/skeleton';
import { StaggerContainer, StaggerItem } from '@/components/animated-layout';
import { useState } from 'react';
import { format } from 'date-fns';

export default function RepositoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const repositoryId = params.id as string;
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Fetch repository details
  const { data: repoData, isLoading: repoLoading, error: repoError, refetch: refetchRepo } = useQuery({
    queryKey: ['repository', repositoryId],
    queryFn: () => repositoriesApi.get(repositoryId),
    enabled: isAuthenticated && !!repositoryId,
  });

  // Fetch analyses
  const { data: analysesData, isLoading: analysesLoading } = useQuery({
    queryKey: ['repository-analyses', repositoryId],
    queryFn: () => analysisApi.list(repositoryId, 5, 0),
    enabled: isAuthenticated && !!repositoryId,
  });

  const repository: Repository | undefined = repoData;
  const analyses: Analysis[] = analysesData?.analyses || [];

  // Handle new analysis
  const handleNewAnalysis = async () => {
    if (!repository) return;
    setIsAnalyzing(true);
    try {
      await analysisApi.create(repository.id, 'full');
      refetchRepo();
    } catch (error) {
      console.error('Failed to start analysis:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-warning-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
              <p className="text-gray-600 mb-4">Please sign in to view repository details.</p>
              <Link href="/">
                <Button>Go to Dashboard</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (repoLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          <Skeleton variant="rectangular" height={200} />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatsCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (repoError || !repository) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Repository Not Found</h2>
              <p className="text-gray-600 mb-4">The repository could not be loaded.</p>
              <Link href="/">
                <Button>Back to Dashboard</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.back()}
                className="mr-2"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                  <GitBranch className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">{repository.full_name}</h1>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    {repository.is_private ? (
                      <span className="flex items-center gap-1">
                        <Lock className="h-3 w-3" /> Private
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Globe className="h-3 w-3" /> Public
                      </span>
                    )}
                    {repository.language && (
                      <span className="badge badge-info">{repository.language}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => refetchRepo()}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button
                onClick={handleNewAnalysis}
                isLoading={isAnalyzing}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                New Analysis
              </Button>
              <Button
                variant="ghost"
                size="icon"
                asChild
              >
                <a href={repository.html_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-5 w-5" />
                </a>
              </Button>
            </div>
          </div>
          
          {repository.description && (
            <p className="mt-4 text-gray-600 dark:text-gray-300">{repository.description}</p>
          )}
          
          {/* Stats */}
          <div className="flex items-center gap-6 mt-4">
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Star className="h-4 w-4 text-yellow-500" />
              <span>{repository.stargazers_count} stars</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <GitFork className="h-4 w-4" />
              <span>{repository.forks_count} forks</span>
            </div>
            {repository.last_analyzed_at && (
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <Calendar className="h-4 w-4" />
                <span>Last analyzed: {format(new Date(repository.last_analyzed_at), 'MMM d, yyyy')}</span>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StaggerItem>
            <Card hover animation="lift" className="h-full">
              <CardHeader className="pb-2">
                <CardDescription>Security Score</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <Star className="h-5 w-5 text-green-600 dark:text-green-400" />
                  </div>
                  <span className="text-2xl font-bold">--</span>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card hover animation="lift" className="h-full">
              <CardHeader className="pb-2">
                <CardDescription>Code Quality</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <CheckCircle2 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <span className="text-2xl font-bold">--</span>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card hover animation="lift" className="h-full">
              <CardHeader className="pb-2">
                <CardDescription>Performance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <Clock className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <span className="text-2xl font-bold">--</span>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card hover animation="lift" className="h-full">
              <CardHeader className="pb-2">
                <CardDescription>CI/CD Health</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-warning-100 dark:bg-warning-900/30 rounded-lg">
                    <Settings className="h-5 w-5 text-warning-600 dark:text-warning-400" />
                  </div>
                  <span className="text-2xl font-bold">--</span>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
        </StaggerContainer>

        {/* Recent Analyses */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Recent Analyses</CardTitle>
              <CardDescription>View past analysis results and recommendations</CardDescription>
            </CardHeader>
            <CardContent>
              {analysesLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} variant="rectangular" height={60} />
                  ))}
                </div>
              ) : analyses.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No analyses yet</h3>
                  <p className="text-gray-500 mb-4">Run your first analysis to get insights about this repository.</p>
                  <Button onClick={handleNewAnalysis} isLoading={isAnalyzing}>
                    <Play className="h-4 w-4 mr-2" />
                    Run Analysis
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {analyses.map((analysis, index) => (
                    <motion.div
                      key={analysis.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                    >
                      <Link href={`/analysis/${analysis.id}`}>
                        <div className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
                          <div className="flex items-center gap-4">
                            <div className={`p-2 rounded-lg ${
                              analysis.status === 'completed' 
                                ? 'bg-green-100 dark:bg-green-900/30' 
                                : analysis.status === 'failed'
                                ? 'bg-red-100 dark:bg-red-900/30'
                                : 'bg-yellow-100 dark:bg-yellow-900/30'
                            }`}>
                              {analysis.status === 'completed' ? (
                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                              ) : analysis.status === 'failed' ? (
                                <AlertCircle className="h-5 w-5 text-red-600" />
                              ) : (
                                <Clock className="h-5 w-5 text-yellow-600" />
                              )}
                            </div>
                            <div>
                              <p className="font-medium">{analysis.analysis_type} Analysis</p>
                              <p className="text-sm text-gray-500">
                                {format(new Date(analysis.created_at), 'MMM d, yyyy h:mm a')}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`badge ${
                              analysis.status === 'completed' ? 'badge-success' :
                              analysis.status === 'failed' ? 'badge-danger' :
                              'badge-warning'
                            }`}>
                              {analysis.status}
                            </span>
                            <ExternalLink className="h-4 w-4 text-gray-400" />
                          </div>
                        </div>
                      </Link>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
