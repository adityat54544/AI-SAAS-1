/**
 * AutoDevOps Workers - Main entry point
 * Background job processing using BullMQ
 */

import 'dotenv/config';
import { Worker, Queue } from 'bullmq';
import IORedis from 'ioredis';
import { analyzeRepository } from './processors/analysis.processor';
import { syncRepository } from './processors/sync.processor';
import { generateCIConfig } from './processors/ci_generation.processor';

const logger = {
  info: (message: string, data?: any) => console.log(JSON.stringify({ level: 'info', message, ...data })),
  error: (message: string, data?: any) => console.error(JSON.stringify({ level: 'error', message, ...data })),
};

// Redis connection
const connection = new IORedis(process.env.REDIS_URL || 'redis://localhost:6379', {
  maxRetriesPerRequest: null,
});

// Queue definitions
export const analysisQueue = new Queue('analysis', { connection });
export const syncQueue = new Queue('sync', { connection });
export const ciGenerationQueue = new Queue('ci_generation', { connection });

// Worker definitions
const workers: Worker[] = [];

async function startWorkers() {
  logger.info('Starting AutoDevOps workers...');

  // Analysis worker
  const analysisWorker = new Worker(
    'analysis',
    async (job) => analyzeRepository(job),
    { 
      connection,
      concurrency: parseInt(process.env.ANALYSIS_CONCURRENCY || '2'),
      limiter: {
        max: 10,
        duration: 60000, // 10 jobs per minute
      },
    }
  );
  
  analysisWorker.on('completed', (job) => {
    logger.info('Analysis job completed', { jobId: job.id, result: job.returnvalue });
  });
  
  analysisWorker.on('failed', (job, err) => {
    logger.error('Analysis job failed', { jobId: job?.id, error: err.message });
  });
  
  workers.push(analysisWorker);

  // Sync worker
  const syncWorker = new Worker(
    'sync',
    async (job) => syncRepository(job),
    { 
      connection,
      concurrency: parseInt(process.env.SYNC_CONCURRENCY || '5'),
    }
  );
  
  syncWorker.on('completed', (job) => {
    logger.info('Sync job completed', { jobId: job.id });
  });
  
  syncWorker.on('failed', (job, err) => {
    logger.error('Sync job failed', { jobId: job?.id, error: err.message });
  });
  
  workers.push(syncWorker);

  // CI Generation worker
  const ciWorker = new Worker(
    'ci_generation',
    async (job) => generateCIConfig(job),
    { 
      connection,
      concurrency: parseInt(process.env.CI_CONCURRENCY || '2'),
    }
  );
  
  ciWorker.on('completed', (job) => {
    logger.info('CI generation job completed', { jobId: job.id });
  });
  
  ciWorker.on('failed', (job, err) => {
    logger.error('CI generation job failed', { jobId: job?.id, error: err.message });
  });
  
  workers.push(ciWorker);

  logger.info('All workers started', { 
    workers: workers.length,
    queues: ['analysis', 'sync', 'ci_generation'],
  });
}

async function shutdown() {
  logger.info('Shutting down workers...');
  
  await Promise.all(workers.map(w => w.close()));
  await connection.quit();
  
  logger.info('Workers shutdown complete');
  process.exit(0);
}

// Handle shutdown signals
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Start workers
startWorkers().catch((error) => {
  logger.error('Failed to start workers', { error: error.message });
  process.exit(1);
});