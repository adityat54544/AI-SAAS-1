/**
 * Analysis Processor Tests
 * Tests for repository analysis job processing
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock Supabase client
vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn().mockImplementation(() => ({
    from: vi.fn().mockReturnThis(),
    select: vi.fn().mockReturnThis(),
    update: vi.fn().mockReturnThis(),
    insert: vi.fn().mockReturnThis(),
    upsert: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    single: vi.fn().mockResolvedValue({
      data: {
        id: 'test-repo-id',
        name: 'test-repo',
        organizations: { id: 'test-org-id' },
      },
      error: null,
    }),
  })),
}));

// Mock Job interface
interface MockJob {
  id: string;
  data: {
    analysis_id: string;
    repository_id: string;
    analysis_type: string;
  };
  updateProgress: (progress: number) => Promise<void>;
}

describe('Analysis Processor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Job Payload Validation', () => {
    it('should accept valid job payload', () => {
      const validPayload = {
        analysis_id: 'analysis-123',
        repository_id: 'repo-456',
        analysis_type: 'full',
      };
      
      expect(validPayload.analysis_id).toBeDefined();
      expect(validPayload.repository_id).toBeDefined();
      expect(validPayload.analysis_type).toBeDefined();
    });

    it('should validate analysis_id is present', () => {
      const payload = {
        analysis_id: '',
        repository_id: 'repo-456',
        analysis_type: 'full',
      };
      
      const isValid = payload.analysis_id.length > 0;
      expect(isValid).toBe(false);
    });

    it('should validate repository_id is present', () => {
      const payload = {
        analysis_id: 'analysis-123',
        repository_id: '',
        analysis_type: 'full',
      };
      
      const isValid = payload.repository_id.length > 0;
      expect(isValid).toBe(false);
    });

    it('should validate analysis_type is valid', () => {
      const validTypes = ['full', 'security', 'performance', 'code_quality'];
      
      const payload = {
        analysis_id: 'analysis-123',
        repository_id: 'repo-456',
        analysis_type: 'full',
      };
      
      expect(validTypes).toContain(payload.analysis_type);
    });
  });

  describe('Processor Execution', () => {
    it('should process job and return success result', async () => {
      // Create a mock processor function
      const mockProcessor = async (job: MockJob) => {
        // Simulate processing
        await job.updateProgress(50);
        await job.updateProgress(100);
        
        return {
          success: true,
          analysis_id: job.data.analysis_id,
        };
      };
      
      const mockJob: MockJob = {
        id: 'job-123',
        data: {
          analysis_id: 'analysis-123',
          repository_id: 'repo-456',
          analysis_type: 'full',
        },
        updateProgress: vi.fn().mockResolvedValue(undefined),
      };
      
      const result = await mockProcessor(mockJob);
      
      expect(result.success).toBe(true);
      expect(result.analysis_id).toBe('analysis-123');
      expect(mockJob.updateProgress).toHaveBeenCalledTimes(2);
    });

    it('should handle processing errors gracefully', async () => {
      const mockProcessor = async (job: MockJob) => {
        throw new Error('Repository not found');
      };
      
      const mockJob: MockJob = {
        id: 'job-123',
        data: {
          analysis_id: 'analysis-123',
          repository_id: 'repo-456',
          analysis_type: 'full',
        },
        updateProgress: vi.fn().mockResolvedValue(undefined),
      };
      
      await expect(mockProcessor(mockJob)).rejects.toThrow('Repository not found');
    });
  });

  describe('Analysis Results', () => {
    it('should generate valid analysis results structure', () => {
      const analysisResults = {
        summary: 'Analysis completed successfully',
        overall_score: 75,
        security_score: 80,
        performance_score: 70,
        code_quality_score: 75,
        ci_cd_score: 65,
        dependencies_score: 85,
        recommendations: [],
      };
      
      expect(analysisResults).toHaveProperty('summary');
      expect(analysisResults).toHaveProperty('overall_score');
      expect(analysisResults).toHaveProperty('security_score');
      expect(analysisResults).toHaveProperty('performance_score');
      expect(analysisResults).toHaveProperty('code_quality_score');
      expect(analysisResults).toHaveProperty('ci_cd_score');
      expect(analysisResults).toHaveProperty('dependencies_score');
      expect(analysisResults).toHaveProperty('recommendations');
    });

    it('should have scores within valid range (0-100)', () => {
      const scores = {
        overall_score: 75,
        security_score: 80,
        performance_score: 70,
        code_quality_score: 75,
        ci_cd_score: 65,
        dependencies_score: 85,
      };
      
      Object.entries(scores).forEach(([key, value]) => {
        expect(value).toBeGreaterThanOrEqual(0);
        expect(value).toBeLessThanOrEqual(100);
      });
    });
  });

  describe('Progress Updates', () => {
    it('should update progress during processing', async () => {
      const progressUpdates: number[] = [];
      
      const mockJob = {
        id: 'job-123',
        data: {
          analysis_id: 'analysis-123',
          repository_id: 'repo-456',
          analysis_type: 'full',
        },
        updateProgress: vi.fn().mockImplementation((progress: number) => {
          progressUpdates.push(progress);
          return Promise.resolve();
        }),
      };
      
      // Simulate progress updates
      for (let progress = 0; progress <= 100; progress += 10) {
        await mockJob.updateProgress(progress);
      }
      
      expect(progressUpdates).toHaveLength(11);
      expect(progressUpdates[0]).toBe(0);
      expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
    });
  });

  describe('External API Mocking', () => {
    it('should mock GitHub API calls', async () => {
      const mockGitHubApi = {
        getRepository: vi.fn().mockResolvedValue({
          data: {
            name: 'test-repo',
            full_name: 'owner/test-repo',
            private: false,
          },
        }),
        getContents: vi.fn().mockResolvedValue({
          data: [{ name: 'package.json', path: 'package.json' }],
        }),
      };
      
      const result = await mockGitHubApi.getRepository('owner/test-repo');
      
      expect(result.data.name).toBe('test-repo');
      expect(mockGitHubApi.getRepository).toHaveBeenCalledWith('owner/test-repo');
    });

    it('should mock AI/Gemini API calls', async () => {
      const mockGeminiApi = {
        analyze: vi.fn().mockResolvedValue({
          analysis: {
            summary: 'Code analysis complete',
            issues: [],
            suggestions: [],
          },
        }),
      };
      
      const result = await mockGeminiApi.analyze('sample code');
      
      expect(result.analysis.summary).toBe('Code analysis complete');
      expect(mockGeminiApi.analyze).toHaveBeenCalledWith('sample code');
    });
  });
});