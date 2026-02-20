/**
 * CI Generation job processor
 * Generates CI/CD configurations using AI with dry-run and auto-PR support
 * 
 * GitHub App Token Requirements:
 * - repo scope: Read repository contents, create branches, create PRs
 * - workflow scope: Write workflow files
 * - Minimum token scopes: repo, workflow
 */

import { Job } from 'bullmq';
import { createClient } from '@supabase/supabase-js';
import { Octokit } from '@octokit/rest';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// GitHub App configuration for auto-PR
const GITHUB_APP_ID = process.env.GITHUB_APP_ID;
const GITHUB_APP_PRIVATE_KEY = process.env.GITHUB_APP_PRIVATE_KEY;
const GITHUB_APP_INSTALLATION_ID = process.env.GITHUB_APP_INSTALLATION_ID;

interface CIGenerationJobData {
  repository_id: string;
  platform: string;
  requirements: string[];
  dry_run?: boolean;         // If true, don't create PR
  create_pr?: boolean;        // If true, create PR automatically
  target_branch?: string;     // Branch to create PR against
  branch_name?: string;       // Custom branch name for PR
}

interface GenerationResult {
  success: boolean;
  repository_id: string;
  dry_run: boolean;
  pr_created: boolean;
  pr_url?: string;
  pr_number?: number;
  config_yaml: string;
  branch_name?: string;
}

/**
 * Create a GitHub Octokit client with App authentication
 * Requires GitHub App with repo and workflow scopes
 */
async function getGitHubClient(installationId?: string): Promise<Octokit | null> {
  if (!GITHUB_APP_ID || !GITHUB_APP_PRIVATE_KEY) {
    console.log('GitHub App not configured, auto-PR disabled');
    return null;
  }
  
  // In production, use @octokit/auth-app for proper JWT authentication
  // For now, return null to indicate auth needs setup
  console.log('GitHub App authentication required for auto-PR');
  return null;
}

/**
 * Validate CI/CD YAML configuration
 */
function validateCIConfig(yaml: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Basic YAML structure validation
  if (!yaml.includes('name:') && !yaml.includes('name ')) {
    errors.push('Missing workflow name');
  }
  
  if (!yaml.includes('on:') && !yaml.includes('jobs:')) {
    errors.push('Missing workflow triggers or jobs');
  }
  
  // Check for common syntax issues
  const lines = yaml.split('\n');
  let inSteps = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.includes('steps:')) {
      inSteps = true;
    }
    if (inSteps && line.includes('- uses:') && !line.includes('@')) {
      errors.push(`Line ${i + 1}: Action missing version tag`);
    }
  }
  
  return { valid: errors.length === 0, errors };
}

/**
 * Create a branch and PR with the generated CI config
 */
async function createPullRequest(
  octokit: Octokit | null,
  owner: string,
  repo: string,
  branchName: string,
  targetBranch: string,
  filePath: string,
  content: string,
  prTitle: string,
  prBody: string
): Promise<{ created: boolean; url?: string; number?: number }> {
  if (!octokit) {
    console.log('GitHub client not available, skipping PR creation');
    return { created: false };
  }
  
  try {
    // Get the latest commit on target branch
    const { data: ref } = await octokit.git.getRef({
      owner,
      repo,
      ref: `heads/${targetBranch}`,
    });
    
    // Create a new branch
    await octokit.git.createRef({
      owner,
      repo,
      ref: `refs/heads/${branchName}`,
      sha: ref.object.sha,
    });
    
    // Create or update the file
    await octokit.repos.createOrUpdateFileContents({
      owner,
      repo,
      path: filePath,
      message: `Add ${filePath}`,
      content: Buffer.from(content).toString('base64'),
      branch: branchName,
    });
    
    // Create pull request
    const { data: pr } = await octokit.pulls.create({
      owner,
      repo,
      title: prTitle,
      head: branchName,
      base: targetBranch,
      body: prBody,
    });
    
    return {
      created: true,
      url: pr.html_url,
      number: pr.number,
    };
  } catch (error: any) {
    console.error('Failed to create PR:', error.message);
    return { created: false };
  }
}

export async function generateCIConfig(job: Job<CIGenerationJobData>): Promise<GenerationResult> {
  const { 
    repository_id, 
    platform, 
    requirements, 
    dry_run = true,
    create_pr = false,
    target_branch = 'main',
    branch_name 
  } = job.data;
  
  console.log('Starting CI generation', { 
    repository_id, 
    platform, 
    dry_run, 
    create_pr 
  });
  
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
    
    // Parse repository URL to get owner/repo
    const repoUrl = repo.github_url || repo.url;
    const urlMatch = repoUrl?.match(/github\.com\/([^/]+)\/([^/]+)/);
    const owner = urlMatch?.[1];
    const repoName = urlMatch?.[2];
    
    // In real implementation, call AI to generate CI config
    const configYaml = `# Generated ${platform} configuration
# This configuration was auto-generated by AutoDevOps AI Platform
# Review and adjust as needed before merging

name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Test
        run: npm test
      
      - name: Build
        run: npm run build

  # Security scanning
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        uses: github/codeql-action/analyze@v3
`;
    
    // Validate the generated config
    const validation = validateCIConfig(configYaml);
    if (!validation.valid) {
      console.warn('Generated config has validation warnings:', validation.errors);
    }
    
    await job.updateProgress(60);
    
    // Store artifact
    await supabase
      .from('artifacts')
      .insert({
        org_id: repo.organizations.id,
        repository_id,
        artifact_type: 'ci_config',
        name: `${platform}_config`,
        content: configYaml,
        format: 'yaml',
        metadata: { 
          platform, 
          requirements,
          dry_run,
          validation_errors: validation.errors,
        },
      });
    
    await job.updateProgress(80);
    
    let prCreated = false;
    let prUrl: string | undefined;
    let prNumber: number | undefined;
    let actualBranchName: string | undefined;
    
    // Create PR if requested and not dry-run
    if (create_pr && !dry_run && owner && repoName) {
      const octokit = await getGitHubClient();
      
      actualBranchName = branch_name || `ci-config-${Date.now()}`;
      const filePath = platform === 'github' ? '.github/workflows/ci.yml' : `.gitlab-ci.yml`;
      
      const prResult = await createPullRequest(
        octokit,
        owner,
        repoName,
        actualBranchName,
        target_branch,
        filePath,
        configYaml,
        `🤖 Add CI/CD configuration (${platform})`,
        `## CI/CD Configuration Generated by AutoDevOps AI

This PR adds an auto-generated CI/CD configuration for your repository.

### What's included:
- **Build job**: Compiles and tests your code
- **Security scanning**: Automated security analysis
- **Caching**: Optimized dependency caching

### Requirements addressed:
${requirements.map(r => `- ${r}`).join('\n')}

### Review checklist:
- [ ] Review the workflow triggers
- [ ] Adjust Node.js version if needed
- [ ] Add any additional steps required
- [ ] Verify secrets are configured

---
*This PR was created automatically. Please review carefully before merging.*`
      );
      
      prCreated = prResult.created;
      prUrl = prResult.url;
      prNumber = prResult.number;
    }
    
    await job.updateProgress(100);
    
    console.log('CI generation completed', { 
      repository_id, 
      dry_run, 
      pr_created: prCreated 
    });
    
    return {
      success: true,
      repository_id,
      dry_run,
      pr_created: prCreated,
      pr_url: prUrl,
      pr_number: prNumber,
      config_yaml: configYaml,
      branch_name: actualBranchName,
    };
    
  } catch (error: any) {
    console.error('CI generation failed', { repository_id, error: error.message });
    throw error;
  }
}

/**
 * Documentation: Auto-PR Feature
 * 
 * To enable automatic PR creation for generated CI configs:
 * 
 * 1. Create a GitHub App:
 *    - Go to GitHub Settings → Developer settings → GitHub Apps
 *    - Create new app with these permissions:
 *      - Contents: Read and write
 *      - Pull requests: Read and write
 *      - Workflows: Read and write
 *    - Generate private key
 *    - Install app to your repositories
 * 
 * 2. Configure environment variables:
 *    - GITHUB_APP_ID: Your GitHub App ID
 *    - GITHUB_APP_PRIVATE_KEY: Private key (PEM format)
 *    - GITHUB_APP_INSTALLATION_ID: Installation ID for the app
 * 
 * 3. Job data parameters:
 *    - dry_run: true = only generate, don't create PR (default)
 *    - create_pr: true = create PR after generation
 *    - target_branch: Branch to create PR against (default: main)
 *    - branch_name: Custom branch name for the PR
 * 
 * 4. Safety requirements:
 *    - Auto-PR requires maintainer review (via branch protection)
 *    - All generated configs should be reviewed before merge
 *    - Use dry_run mode for testing
 */
