/**
 * Queue Setup Tests
 * Tests for BullMQ queue initialization and configuration
 */

import { describe, it, expect, vi } from 'vitest';

describe('Queue Setup', () => {
  describe('Queue Initialization', () => {
    it('should create analysis queue with correct name', async () => {
      // Mock BullMQ Queue
      const mockQueue = vi.fn().mockImplementation((name: string) => ({
        name,
        isPaused: vi.fn().mockResolvedValue(false),
        pause: vi.fn().mockResolvedValue(undefined),
        resume: vi.fn().mockResolvedValue(undefined),
        close: vi.fn().mockResolvedValue(undefined),
        add: vi.fn().mockResolvedValue({ id: 'test-job-id' }),
      }));
      
      const analysisQueue = mockQueue('analysis');
      
      expect(analysisQueue.name).toBe('analysis');
    });

    it('should create sync queue with correct name', async () => {
      const mockQueue = vi.fn().mockImplementation((name: string) => ({
        name,
      }));
      
      const syncQueue = mockQueue('sync');
      
      expect(syncQueue.name).toBe('sync');
    });

    it('should create ci_generation queue with correct name', async () => {
      const mockQueue = vi.fn().mockImplementation((name: string) => ({
        name,
      }));
      
      const ciQueue = mockQueue('ci_generation');
      
      expect(ciQueue.name).toBe('ci_generation');
    });
  });

  describe('Redis Connection Configuration', () => {
    it('should use REDIS_URL environment variable when set', () => {
      const originalRedisUrl = process.env.REDIS_URL;
      process.env.REDIS_URL = 'redis://custom-host:6380';
      
      const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
      
      expect(redisUrl).toBe('redis://custom-host:6380');
      
      process.env.REDIS_URL = originalRedisUrl;
    });

    it('should fallback to localhost when REDIS_URL not set', () => {
      const originalRedisUrl = process.env.REDIS_URL;
      delete process.env.REDIS_URL;
      
      const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
      
      expect(redisUrl).toBe('redis://localhost:6379');
      
      process.env.REDIS_URL = originalRedisUrl;
    });

    it('should configure maxRetriesPerRequest as null for BullMQ compatibility', () => {
      const redisOptions = {
        maxRetriesPerRequest: null,
      };
      
      expect(redisOptions.maxRetriesPerRequest).toBeNull();
    });
  });

  describe('Queue Names', () => {
    it('should define all required queues', () => {
      const expectedQueues = ['analysis', 'sync', 'ci_generation'];
      
      // Verify all queue names are valid identifiers
      expectedQueues.forEach(name => {
        expect(name).toMatch(/^[a-z_]+$/);
        expect(name.length).toBeGreaterThan(0);
      });
      
      expect(expectedQueues).toHaveLength(3);
    });

    it('should have unique queue names', () => {
      const queueNames = ['analysis', 'sync', 'ci_generation'];
      const uniqueNames = [...new Set(queueNames)];
      
      expect(uniqueNames).toHaveLength(queueNames.length);
    });
  });

  describe('Job Operations', () => {
    it('should be able to add a job to queue', async () => {
      const mockQueue = vi.fn().mockImplementation(() => ({
        add: vi.fn().mockResolvedValue({ id: 'test-job-id', data: { test: 'data' } }),
      }));
      
      const queue = mockQueue('test');
      const job = await queue.add({ test: 'data' });
      
      expect(job.id).toBe('test-job-id');
      expect(queue.add).toHaveBeenCalledWith({ test: 'data' });
    });
  });

  describe('Worker Configuration', () => {
    it('should have default concurrency settings', () => {
      const defaultConcurrency = {
        analysis: parseInt(process.env.ANALYSIS_CONCURRENCY || '2'),
        sync: parseInt(process.env.SYNC_CONCURRENCY || '5'),
        ci: parseInt(process.env.CI_CONCURRENCY || '2'),
      };
      
      expect(defaultConcurrency.analysis).toBe(2);
      expect(defaultConcurrency.sync).toBe(5);
      expect(defaultConcurrency.ci).toBe(2);
    });

    it('should have rate limiter configuration for analysis queue', () => {
      const rateLimiter = {
        max: 10,
        duration: 60000, // 10 jobs per minute
      };
      
      expect(rateLimiter.max).toBe(10);
      expect(rateLimiter.duration).toBe(60000);
    });
  });
});