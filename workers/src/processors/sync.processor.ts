/**
 * Sync job processor
 * Syncs repository metadata from GitHub
 */

import { Job } from 'bullmq';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

interface SyncJobData {
  repository_id: string;
  trigger: string;
}

export async function syncRepository(job: Job<SyncJobData>) {
  const { repository_id, trigger } = job.data;
  
  console.log('Starting sync', { repository_id, trigger });
  
  try {
    await job.updateProgress(10);
    
    // Get repository details
    const { data: repo } = await supabase
      .from('repositories')
      .select('*, organizations!inner(id)')
      .eq('id', repository_id)
      .single();
    
    if (!repo) {
      throw new Error('Repository not found');
    }
    
    await job.updateProgress(30);
    
    // In real implementation, fetch latest data from GitHub API
    // and update the repository record
    
    await job.updateProgress(70);
    
    // Update last_synced_at
    await supabase
      .from('repositories')
      .update({ 
        updated_at: new Date().toISOString(),
      })
      .eq('id', repository_id);
    
    await job.updateProgress(100);
    
    console.log('Sync completed', { repository_id });
    
    return { success: true, repository_id };
    
  } catch (error: any) {
    console.error('Sync failed', { repository_id, error: error.message });
    throw error;
  }
}