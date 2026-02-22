-- ============================================================================
-- AutoDevOps AI Platform - Robust Migration Script
-- Version: 3.0.0 (Handles Partial/Existing Schema)
-- ============================================================================

-- ============================================================================
-- STEP 1: CORE FUNCTIONS (Always run first)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Helper function to add column if not exists
CREATE OR REPLACE FUNCTION public.add_column_if_not_exists(
    p_table_name text,
    p_column_name text,
    p_column_definition text
) RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema = 'public' 
        AND c.table_name = p_table_name 
        AND c.column_name = p_column_name
    ) THEN
        EXECUTE format('ALTER TABLE public.%I ADD COLUMN %I %s', 
            p_table_name, p_column_name, p_column_definition);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 2: USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users are viewable by everyone" ON public.users;
CREATE POLICY "Users are viewable by everyone"
ON public.users FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can be inserted by anyone" ON public.users;
CREATE POLICY "Users can be inserted by anyone"
ON public.users FOR INSERT WITH CHECK (true);

-- ============================================================================
-- STEP 3: ORGANIZATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    github_id INTEGER,
    avatar_url TEXT,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    plan TEXT DEFAULT 'free',
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add missing columns if they don't exist (using DO block to avoid JSON output)
DO $$
BEGIN
    PERFORM public.add_column_if_not_exists('organizations', 'github_id', 'INTEGER');
    PERFORM public.add_column_if_not_exists('organizations', 'avatar_url', 'TEXT');
    PERFORM public.add_column_if_not_exists('organizations', 'description', 'TEXT');
    PERFORM public.add_column_if_not_exists('organizations', 'plan', 'TEXT DEFAULT ''free''');
    PERFORM public.add_column_if_not_exists('organizations', 'settings', 'JSONB DEFAULT ''{}''::jsonb');
END $$;

CREATE INDEX IF NOT EXISTS idx_organizations_owner_id ON public.organizations(owner_id);
CREATE INDEX IF NOT EXISTS idx_organizations_github_id ON public.organizations(github_id);

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 4: ORGANIZATION MEMBERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    invited_by UUID REFERENCES public.users(id),
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(org_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON public.organization_members(org_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON public.organization_members(user_id);

ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view members of their organizations" ON public.organization_members;
CREATE POLICY "Users can view members of their organizations"
ON public.organization_members FOR SELECT USING (
    user_id = auth.uid()
    OR EXISTS (
        SELECT 1 FROM public.organization_members om
        WHERE om.org_id = organization_members.org_id AND om.user_id = auth.uid()
    )
    OR EXISTS (
        SELECT 1 FROM public.organizations WHERE id = org_id AND owner_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Organization owners can manage members" ON public.organization_members;
CREATE POLICY "Organization owners can manage members"
ON public.organization_members FOR ALL USING (
    EXISTS (SELECT 1 FROM public.organizations WHERE id = org_id AND owner_id = auth.uid())
);

-- ============================================================================
-- STEP 5: ORGANIZATION POLICIES
-- ============================================================================

DROP POLICY IF EXISTS "Users can view their organizations" ON public.organizations;
CREATE POLICY "Users can view their organizations"
ON public.organizations FOR SELECT USING (
    owner_id = auth.uid()
    OR EXISTS (
        SELECT 1 FROM public.organization_members
        WHERE org_id = id AND user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Only owner can update organization" ON public.organizations;
CREATE POLICY "Only owner can update organization"
ON public.organizations FOR UPDATE USING (owner_id = auth.uid());

DROP POLICY IF EXISTS "Users can create organizations" ON public.organizations;
CREATE POLICY "Users can create organizations"
ON public.organizations FOR INSERT WITH CHECK (owner_id = auth.uid());

DROP TRIGGER IF EXISTS update_organizations_updated_at ON public.organizations;
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 6: REPOSITORIES TABLE (With All Columns)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    github_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    description TEXT,
    html_url TEXT NOT NULL,
    language TEXT,
    stargazers_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    is_private BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    default_branch TEXT DEFAULT 'main',
    topics TEXT[] DEFAULT '{}',
    webhook_id INTEGER,
    webhook_secret TEXT,
    last_analyzed_at TIMESTAMPTZ,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(org_id, github_id)
);

-- Add missing columns to repositories if table already existed (using DO block to avoid JSON output)
DO $$
BEGIN
    PERFORM public.add_column_if_not_exists('repositories', 'description', 'TEXT');
    PERFORM public.add_column_if_not_exists('repositories', 'language', 'TEXT');
    PERFORM public.add_column_if_not_exists('repositories', 'stargazers_count', 'INTEGER DEFAULT 0');
    PERFORM public.add_column_if_not_exists('repositories', 'forks_count', 'INTEGER DEFAULT 0');
    PERFORM public.add_column_if_not_exists('repositories', 'is_private', 'BOOLEAN DEFAULT false');
    PERFORM public.add_column_if_not_exists('repositories', 'default_branch', 'TEXT DEFAULT ''main''');
    PERFORM public.add_column_if_not_exists('repositories', 'topics', 'TEXT[] DEFAULT ''{}''');
    PERFORM public.add_column_if_not_exists('repositories', 'webhook_id', 'INTEGER');
    PERFORM public.add_column_if_not_exists('repositories', 'webhook_secret', 'TEXT');
    PERFORM public.add_column_if_not_exists('repositories', 'last_analyzed_at', 'TIMESTAMPTZ');
    PERFORM public.add_column_if_not_exists('repositories', 'settings', 'JSONB DEFAULT ''{}''::jsonb');
END $$;

CREATE INDEX IF NOT EXISTS idx_repositories_org_id ON public.repositories(org_id);
CREATE INDEX IF NOT EXISTS idx_repositories_github_id ON public.repositories(github_id);
CREATE INDEX IF NOT EXISTS idx_repositories_is_active ON public.repositories(is_active);
CREATE INDEX IF NOT EXISTS idx_repositories_last_analyzed ON public.repositories(last_analyzed_at);

ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view repositories in their organizations" ON public.repositories;
CREATE POLICY "Users can view repositories in their organizations"
ON public.repositories FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.organizations
        WHERE id = org_id AND (
            owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = organizations.id AND user_id = auth.uid()
            )
        )
    )
);

DROP POLICY IF EXISTS "Users can create repositories" ON public.repositories;
CREATE POLICY "Users can create repositories"
ON public.repositories FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.organizations
        WHERE id = org_id AND owner_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can update repositories" ON public.repositories;
CREATE POLICY "Users can update repositories"
ON public.repositories FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM public.organizations
        WHERE id = org_id AND owner_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can delete repositories" ON public.repositories;
CREATE POLICY "Users can delete repositories"
ON public.repositories FOR DELETE USING (
    EXISTS (
        SELECT 1 FROM public.organizations
        WHERE id = org_id AND owner_id = auth.uid()
    )
);

DROP TRIGGER IF EXISTS update_repositories_updated_at ON public.repositories;
CREATE TRIGGER update_repositories_updated_at
    BEFORE UPDATE ON public.repositories
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 7: REPOSITORY HEALTH TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.repository_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    overall_score DECIMAL(5,2) DEFAULT 0,
    security_score DECIMAL(5,2) DEFAULT 0,
    performance_score DECIMAL(5,2) DEFAULT 0,
    code_quality_score DECIMAL(5,2) DEFAULT 0,
    ci_cd_score DECIMAL(5,2) DEFAULT 0,
    dependencies_score DECIMAL(5,2) DEFAULT 0,
    metrics JSONB DEFAULT '{}'::jsonb,
    analysis_timestamp TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(repository_id)
);

CREATE INDEX IF NOT EXISTS idx_repository_health_repo_id ON public.repository_health(repository_id);

ALTER TABLE public.repository_health ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view health of accessible repositories" ON public.repository_health;
CREATE POLICY "Users can view health of accessible repositories"
ON public.repository_health FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.repositories r
        JOIN public.organizations o ON o.id = r.org_id
        WHERE r.id = repository_id AND (
            o.owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = o.id AND user_id = auth.uid()
            )
        )
    )
);

-- ============================================================================
-- STEP 8: ANALYSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    analysis_type TEXT NOT NULL DEFAULT 'full',
    triggered_by UUID REFERENCES public.users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    results JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add missing columns if table existed (using DO block to avoid JSON output)
DO $$
BEGIN
    PERFORM public.add_column_if_not_exists('analyses', 'analysis_type', 'TEXT NOT NULL DEFAULT ''full''');
    PERFORM public.add_column_if_not_exists('analyses', 'triggered_by', 'UUID REFERENCES public.users(id) ON DELETE CASCADE');
    PERFORM public.add_column_if_not_exists('analyses', 'started_at', 'TIMESTAMPTZ');
    PERFORM public.add_column_if_not_exists('analyses', 'completed_at', 'TIMESTAMPTZ');
    PERFORM public.add_column_if_not_exists('analyses', 'error_message', 'TEXT');
END $$;

-- Add check constraints safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'analyses_status_check'
    ) THEN
        ALTER TABLE public.analyses ADD CONSTRAINT analyses_status_check 
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'));
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'analyses_analysis_type_check'
    ) THEN
        ALTER TABLE public.analyses ADD CONSTRAINT analyses_analysis_type_check 
        CHECK (analysis_type IN ('full', 'security', 'performance', 'ci_cd'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_analyses_repository_id ON public.analyses(repository_id);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON public.analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_triggered_by ON public.analyses(triggered_by);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON public.analyses(created_at DESC);

ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view analyses for accessible repositories" ON public.analyses;
CREATE POLICY "Users can view analyses for accessible repositories"
ON public.analyses FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.repositories r
        JOIN public.organizations o ON o.id = r.org_id
        WHERE r.id = repository_id AND (
            o.owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = o.id AND user_id = auth.uid()
            )
        )
    )
);

DROP POLICY IF EXISTS "Users can create analyses" ON public.analyses;
CREATE POLICY "Users can create analyses"
ON public.analyses FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.repositories r
        JOIN public.organizations o ON o.id = r.org_id
        WHERE r.id = repository_id AND (
            o.owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = o.id AND user_id = auth.uid()
            )
        )
    )
);

DROP TRIGGER IF EXISTS update_analyses_updated_at ON public.analyses;
CREATE TRIGGER update_analyses_updated_at
    BEFORE UPDATE ON public.analyses
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 9: RECOMMENDATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
    category TEXT NOT NULL DEFAULT 'general',
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    suggested_fix TEXT,
    is_dismissed BOOLEAN DEFAULT false,
    dismissed_by UUID REFERENCES public.users(id),
    dismissed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add check constraints safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'recommendations_category_check'
    ) THEN
        ALTER TABLE public.recommendations ADD CONSTRAINT recommendations_category_check 
        CHECK (category IN ('security', 'performance', 'code_quality', 'ci_cd', 'dependencies', 'general'));
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'recommendations_severity_check'
    ) THEN
        ALTER TABLE public.recommendations ADD CONSTRAINT recommendations_severity_check 
        CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_recommendations_analysis_id ON public.recommendations(analysis_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_category ON public.recommendations(category);
CREATE INDEX IF NOT EXISTS idx_recommendations_severity ON public.recommendations(severity);
CREATE INDEX IF NOT EXISTS idx_recommendations_file_path ON public.recommendations(file_path);

ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view recommendations for accessible analyses" ON public.recommendations;
CREATE POLICY "Users can view recommendations for accessible analyses"
ON public.recommendations FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.analyses a
        JOIN public.repositories r ON r.id = a.repository_id
        JOIN public.organizations o ON o.id = r.org_id
        WHERE a.id = analysis_id AND (
            o.owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = o.id AND user_id = auth.uid()
            )
        )
    )
);

-- ============================================================================
-- STEP 10: REMEDIATION SNIPPETS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.remediation_snippets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    original_code TEXT NOT NULL,
    suggested_code TEXT NOT NULL,
    explanation TEXT,
    apply_status TEXT DEFAULT 'pending',
    applied_by UUID REFERENCES public.users(id),
    applied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add check constraint safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'remediation_snippets_apply_status_check'
    ) THEN
        ALTER TABLE public.remediation_snippets ADD CONSTRAINT remediation_snippets_apply_status_check 
        CHECK (apply_status IN ('pending', 'applied', 'rejected'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_remediation_analysis_id ON public.remediation_snippets(analysis_id);

ALTER TABLE public.remediation_snippets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view remediation snippets for accessible analyses" ON public.remediation_snippets;
CREATE POLICY "Users can view remediation snippets for accessible analyses"
ON public.remediation_snippets FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.analyses a
        JOIN public.repositories r ON r.id = a.repository_id
        JOIN public.organizations o ON o.id = r.org_id
        WHERE a.id = analysis_id AND (
            o.owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = o.id AND user_id = auth.uid()
            )
        )
    )
);

-- ============================================================================
-- STEP 11: JOBS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL DEFAULT 'analysis',
    status TEXT NOT NULL DEFAULT 'queued',
    repository_id UUID REFERENCES public.repositories(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    payload JSONB,
    result_data JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add missing columns (using DO block to avoid JSON output)
DO $$
BEGIN
    PERFORM public.add_column_if_not_exists('jobs', 'progress', 'INTEGER DEFAULT 0');
    PERFORM public.add_column_if_not_exists('jobs', 'error_message', 'TEXT');
    PERFORM public.add_column_if_not_exists('jobs', 'started_at', 'TIMESTAMPTZ');
    PERFORM public.add_column_if_not_exists('jobs', 'completed_at', 'TIMESTAMPTZ');
END $$;

-- Add check constraints safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'jobs_job_type_check'
    ) THEN
        ALTER TABLE public.jobs ADD CONSTRAINT jobs_job_type_check 
        CHECK (job_type IN ('analysis', 'clone', 'sync', 'ci_generation'));
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'jobs_status_check'
    ) THEN
        ALTER TABLE public.jobs ADD CONSTRAINT jobs_status_check 
        CHECK (status IN ('queued', 'processing', 'completed', 'failed'));
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'jobs_progress_check'
    ) THEN
        ALTER TABLE public.jobs ADD CONSTRAINT jobs_progress_check 
        CHECK (progress >= 0 AND progress <= 100);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_jobs_repository_id ON public.jobs(repository_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON public.jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON public.jobs(created_at DESC);

ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view jobs for accessible repositories" ON public.jobs;
CREATE POLICY "Users can view jobs for accessible repositories"
ON public.jobs FOR SELECT USING (
    repository_id IS NULL OR EXISTS (
        SELECT 1 FROM public.repositories r
        JOIN public.organizations o ON o.id = r.org_id
        WHERE r.id = repository_id AND (
            o.owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = o.id AND user_id = auth.uid()
            )
        )
    )
);

DROP POLICY IF EXISTS "Service role can manage all jobs" ON public.jobs;
CREATE POLICY "Service role can manage all jobs"
ON public.jobs FOR ALL USING (auth.role() = 'service_role');

DROP TRIGGER IF EXISTS update_jobs_updated_at ON public.jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON public.jobs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 12: JOB LOGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    level TEXT NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add check constraint safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'job_logs_level_check'
    ) THEN
        ALTER TABLE public.job_logs ADD CONSTRAINT job_logs_level_check 
        CHECK (level IN ('debug', 'info', 'warning', 'error'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON public.job_logs(job_id);
CREATE INDEX IF NOT EXISTS idx_job_logs_created_at ON public.job_logs(created_at DESC);

ALTER TABLE public.job_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view logs for accessible jobs" ON public.job_logs;
CREATE POLICY "Users can view logs for accessible jobs"
ON public.job_logs FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.jobs j
        WHERE j.id = job_id AND (
            j.repository_id IS NULL OR EXISTS (
                SELECT 1 FROM public.repositories r
                JOIN public.organizations o ON o.id = r.org_id
                WHERE r.id = j.repository_id AND (
                    o.owner_id = auth.uid()
                    OR EXISTS (
                        SELECT 1 FROM public.organization_members
                        WHERE org_id = o.id AND user_id = auth.uid()
                    )
                )
            )
        )
    )
);

-- ============================================================================
-- STEP 13: GITHUB TOKENS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.github_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_type TEXT DEFAULT 'Bearer',
    scope TEXT,
    expires_at TIMESTAMPTZ,
    github_user_id INTEGER,
    github_username TEXT,
    is_valid BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, org_id)
);

-- Add missing columns (using DO block to avoid JSON output)
DO $$
BEGIN
    PERFORM public.add_column_if_not_exists('github_tokens', 'refresh_token_encrypted', 'TEXT');
    PERFORM public.add_column_if_not_exists('github_tokens', 'token_type', 'TEXT DEFAULT ''Bearer''');
    PERFORM public.add_column_if_not_exists('github_tokens', 'scope', 'TEXT');
    PERFORM public.add_column_if_not_exists('github_tokens', 'expires_at', 'TIMESTAMPTZ');
    PERFORM public.add_column_if_not_exists('github_tokens', 'github_user_id', 'INTEGER');
    PERFORM public.add_column_if_not_exists('github_tokens', 'github_username', 'TEXT');
    PERFORM public.add_column_if_not_exists('github_tokens', 'is_valid', 'BOOLEAN DEFAULT true');
    PERFORM public.add_column_if_not_exists('github_tokens', 'last_used_at', 'TIMESTAMPTZ');
END $$;

CREATE INDEX IF NOT EXISTS idx_github_tokens_user_id ON public.github_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_github_tokens_org_id ON public.github_tokens(org_id);

ALTER TABLE public.github_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own tokens" ON public.github_tokens;
CREATE POLICY "Users can view their own tokens"
ON public.github_tokens FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can insert their own tokens" ON public.github_tokens;
CREATE POLICY "Users can insert their own tokens"
ON public.github_tokens FOR INSERT WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update their own tokens" ON public.github_tokens;
CREATE POLICY "Users can update their own tokens"
ON public.github_tokens FOR UPDATE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete their own tokens" ON public.github_tokens;
CREATE POLICY "Users can delete their own tokens"
ON public.github_tokens FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Service role can manage all tokens" ON public.github_tokens;
CREATE POLICY "Service role can manage all tokens"
ON public.github_tokens FOR ALL USING (auth.role() = 'service_role');

DROP TRIGGER IF EXISTS update_github_tokens_updated_at ON public.github_tokens;
CREATE TRIGGER update_github_tokens_updated_at
    BEFORE UPDATE ON public.github_tokens
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 14: ARTIFACTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES public.repositories(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL DEFAULT 'ci_config',
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'yaml',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add check constraints safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'artifacts_artifact_type_check'
    ) THEN
        ALTER TABLE public.artifacts ADD CONSTRAINT artifacts_artifact_type_check 
        CHECK (artifact_type IN ('ci_config', 'security_report', 'performance_report', 'code_report', 'dependency_report'));
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'artifacts_format_check'
    ) THEN
        ALTER TABLE public.artifacts ADD CONSTRAINT artifacts_format_check 
        CHECK (format IN ('yaml', 'json', 'markdown', 'html'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_artifacts_org_id ON public.artifacts(org_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_repository_id ON public.artifacts(repository_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_analysis_id ON public.artifacts(analysis_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON public.artifacts(artifact_type);

ALTER TABLE public.artifacts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view artifacts in their organizations" ON public.artifacts;
CREATE POLICY "Users can view artifacts in their organizations"
ON public.artifacts FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.organizations
        WHERE id = org_id AND (
            owner_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.organization_members
                WHERE org_id = organizations.id AND user_id = auth.uid()
            )
        )
    )
);

DROP POLICY IF EXISTS "Users can create artifacts in their organizations" ON public.artifacts;
CREATE POLICY "Users can create artifacts in their organizations"
ON public.artifacts FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.organizations
        WHERE id = org_id AND owner_id = auth.uid()
    )
);

DROP TRIGGER IF EXISTS update_artifacts_updated_at ON public.artifacts;
CREATE TRIGGER update_artifacts_updated_at
    BEFORE UPDATE ON public.artifacts
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- CLEANUP: Drop helper function (optional)
-- ============================================================================

-- Drop the helper function if you don't want it to remain in the database
-- DROP FUNCTION IF EXISTS public.add_column_if_not_exists(text, text, text);

-- ============================================================================
-- VERIFICATION QUERIES (Run separately after deployment)
-- ============================================================================

-- Verify tables exist:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;

-- Verify columns in repositories table:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'repositories';

-- Verify RLS policies:
-- SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename;