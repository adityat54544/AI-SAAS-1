'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Clock,
  Shield,
  Zap,
  Code2,
  Settings,
  Package,
  FileCode,
  ChevronRight,
  X,
  ExternalLink,
  Loader2
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { analysisApi, Recommendation, Remediation, Analysis } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const analysisId = params.id as string;
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [filter, setFilter] = useState<string>('all');

  // Fetch analysis details
  const { data: analysisData, isLoading: analysisLoading, error: analysisError } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => analysisApi.get(analysisId),
    enabled: isAuthenticated && !!analysisId,
  });

  // Fetch recommendations
  const { data: recommendationsData, isLoading: recommendationsLoading } = useQuery({
    queryKey: ['analysis-recommendations', analysisId],
    queryFn: () => analysisApi.getRecommendations(analysisId),
    enabled: isAuthenticated && !!analysisId,
  });

  // Fetch remediations
  const { data: remediationsData, isLoading: remediationsLoading } = useQuery({
    queryKey: ['analysis-remediations', analysisId],
    queryFn: () => analysisApi.getRemediations(analysisId),
    enabled: isAuthenticated && !!analysisId,
  });

  const analysis: Analysis | undefined = analysisData?.analysis;
  const recommendations: Recommendation[] = recommendationsData?.recommendations || [];
  const remediations: Remediation[] = remediationsData?.remediations || [];

  // Filter recommendations
  const filteredRecommendations = filter === 'all' 
    ? recommendations 
    : recommendations.filter(r => r.category === filter);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100 dark:bg-red-900/30';
      case 'high': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
      case 'low': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-800';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'security': return <Shield className="h-4 w-4" />;
      case 'performance': return <Zap className="h-4 w-4" />;
      case 'code_quality': return <Code2 className="h-4 w-4" />;
      case 'ci_cd': return <Settings className="h-4 w-4" />;
      case 'dependencies': return <Package className="h-4 w-4" />;
      default: return <FileCode className="h-4 w-4" />;
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
              <p className="text-gray-600 mb-4">Please sign in to view analysis details.</p>
              <Link href="/">
                <Button>Go to Dashboard</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (analysisLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          <Skeleton variant="rectangular" height={100} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} variant="rectangular" height={120} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (analysisError || !analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Analysis Not Found</h2>
              <p className="text-gray-600 mb-4">The analysis could not be loaded.</p>
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
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${
                  analysis.status === 'completed' 
                    ? 'bg-green-100 dark:bg-green-900/30' 
                    : analysis.status === 'failed'
                    ? 'bg-red-100 dark:bg-red-900/30'
                    : 'bg-yellow-100 dark:bg-yellow-900/30'
                }`}>
                  {analysis.status === 'completed' ? (
                    <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
                  ) : analysis.status === 'failed' ? (
                    <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
                  ) : (
                    <Loader2 className="h-6 w-6 text-yellow-600 dark:text-yellow-400 animate-spin" />
                  )}
                </div>
                <div>
                  <h1 className="text-2xl font-bold">{analysis.analysis_type} Analysis</h1>
                  <p className="text-sm text-gray-500">
                    Created {format(new Date(analysis.created_at), 'MMM d, yyyy h:mm a')}
                  </p>
                </div>
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
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Category Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"
        >
          {['security', 'performance', 'code_quality', 'ci_cd', 'dependencies'].map((category, index) => {
            const count = recommendations.filter(r => r.category === category).length;
            return (
              <motion.div
                key={category}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <Card 
                  hover 
                  animation={filter === category ? 'lift' : 'none'}
                  className={`cursor-pointer transition-colors ${filter === category ? 'ring-2 ring-primary-500' : ''}`}
                  onClick={() => setFilter(filter === category ? 'all' : category)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        {getCategoryIcon(category)}
                      </div>
                      <div>
                        <p className="text-2xl font-bold">{count}</p>
                        <p className="text-xs text-gray-500 capitalize">{category.replace('_', ' ')}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Recommendations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Recommendations ({filteredRecommendations.length})</CardTitle>
              <CardDescription>
                {filter !== 'all' 
                  ? `Showing ${filter.replace('_', ' ')} recommendations`
                  : 'AI-powered recommendations to improve your repository'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recommendationsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} variant="rectangular" height={80} />
                  ))}
                </div>
              ) : filteredRecommendations.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No recommendations</h3>
                  <p className="text-gray-500">
                    {filter !== 'all' 
                      ? 'No recommendations found for this category.'
                      : 'Great job! No issues found in this analysis.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <AnimatePresence mode="popLayout">
                    {filteredRecommendations.map((recommendation, index) => (
                      <motion.div
                        key={recommendation.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2, delay: index * 0.03 }}
                        className="flex items-start gap-4 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                        onClick={() => setSelectedRecommendation(recommendation)}
                      >
                        <div className={`p-2 rounded-lg ${getSeverityColor(recommendation.severity)}`}>
                          {getCategoryIcon(recommendation.category)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium truncate">{recommendation.title}</h4>
                            <span className={`badge text-xs ${getSeverityColor(recommendation.severity)}`}>
                              {recommendation.severity}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 line-clamp-2">{recommendation.description}</p>
                          {recommendation.file_path && (
                            <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                              <FileCode className="h-3 w-3" />
                              {recommendation.file_path}
                              {recommendation.line_number && `:${recommendation.line_number}`}
                            </p>
                          )}
                        </div>
                        <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0" />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recommendation Detail Modal */}
      <AnimatePresence>
        {selectedRecommendation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
            onClick={() => setSelectedRecommendation(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${getSeverityColor(selectedRecommendation.severity)}`}>
                    {getCategoryIcon(selectedRecommendation.category)}
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold">{selectedRecommendation.title}</h2>
                    <p className="text-sm text-gray-500 capitalize">
                      {selectedRecommendation.category.replace('_', ' ')} • {selectedRecommendation.severity}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedRecommendation(null)}
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="mb-6">
                  <h3 className="font-medium mb-2">Description</h3>
                  <p className="text-gray-600 dark:text-gray-300">{selectedRecommendation.description}</p>
                </div>
                {selectedRecommendation.file_path && (
                  <div className="mb-6">
                    <h3 className="font-medium mb-2">Location</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <FileCode className="h-4 w-4" />
                      <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                        {selectedRecommendation.file_path}
                        {selectedRecommendation.line_number && `:${selectedRecommendation.line_number}`}
                      </code>
                    </div>
                  </div>
                )}
                {selectedRecommendation.suggested_fix && (
                  <div>
                    <h3 className="font-medium mb-2">Suggested Fix</h3>
                    <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm">
                      <code>{selectedRecommendation.suggested_fix}</code>
                    </pre>
                  </div>
                )}
              </div>
              <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
                <Button variant="outline" onClick={() => setSelectedRecommendation(null)}>
                  Close
                </Button>
                <Button>
                  Apply Fix
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
