-- Create repositories table
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
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(org_id, github_id)
);

-- Create indexes
CREATE INDEX idx_repositories_org_id ON public.repositories(org_id);
CREATE INDEX idx_repositories_github_id ON public.repositories(github_id);
CREATE INDEX idx_repositories_is_active ON public.repositories(is_active);
CREATE INDEX idx_repositories_last_analyzed ON public.repositories(last_analyzed_at);

-- Enable Row Level Security
ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view repositories in their organizations
CREATE POLICY "Users can view repositories in their organizations" ON public.repositories
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.organizations 
            WHERE id = org_id AND (
                owner_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM public.organization_members 
                    WHERE org_id = organizations.id AND user_id = auth.uid()
                )
            )
        )
    );

-- Policy: Users can insert repositories in their organizations
CREATE POLICY "Users can create repositories" ON public.repositories
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.organizations 
            WHERE id = org_id AND owner_id = auth.uid()
        )
    );

-- Policy: Users can update repositories in their organizations
CREATE POLICY "Users can update repositories" ON public.repositories
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.organizations 
            WHERE id = org_id AND owner_id = auth.uid()
        )
    );

-- Policy: Users can delete repositories in their organizations
CREATE POLICY "Users can delete repositories" ON public.repositories
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.organizations 
            WHERE id = org_id AND owner_id = auth.uid()
        )
    );

-- Create updated_at trigger
CREATE TRIGGER update_repositories_updated_at
    BEFORE UPDATE ON public.repositories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create repository_health table for storing health scores
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
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(repository_id)
);

CREATE INDEX idx_repository_health_repo_id ON public.repository_health(repository_id);

-- Enable RLS on repository_health
ALTER TABLE public.repository_health ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view health of accessible repositories" ON public.repository_health
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.repositories r
            JOIN public.organizations o ON o.id = r.org_id
            WHERE r.id = repository_id AND (
                o.owner_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM public.organization_members 
                    WHERE org_id = o.id AND user_id = auth.uid()
                )
            )
        )
    );