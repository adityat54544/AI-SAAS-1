-- Create organization_members table for multi-tenant access
CREATE TABLE IF NOT EXISTS public.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    invited_by UUID REFERENCES public.users(id),
    invited_at TIMESTAMP WITH TIME ZONE,
    accepted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(org_id, user_id)
);

CREATE INDEX idx_org_members_org_id ON public.organization_members(org_id);
CREATE INDEX idx_org_members_user_id ON public.organization_members(user_id);

-- Enable RLS
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view members of their organizations" ON public.organization_members
    FOR SELECT USING (
        org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid())
        OR user_id = auth.uid()
        OR EXISTS (
            SELECT 1 FROM public.organization_members om
            WHERE om.org_id = organization_members.org_id AND om.user_id = auth.uid()
        )
    );

CREATE POLICY "Organization owners can manage members" ON public.organization_members
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.organizations WHERE id = org_id AND owner_id = auth.uid())
    );

-- Create github_tokens table for encrypted token storage
CREATE TABLE IF NOT EXISTS public.github_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_type TEXT DEFAULT 'Bearer',
    scope TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    github_user_id INTEGER,
    github_username TEXT,
    is_valid BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, org_id)
);

CREATE INDEX idx_github_tokens_user_id ON public.github_tokens(user_id);
CREATE INDEX idx_github_tokens_org_id ON public.github_tokens(org_id);

-- Enable RLS
ALTER TABLE public.github_tokens ENABLE ROW LEVEL SECURITY;

-- Users can only see their own tokens
CREATE POLICY "Users can view their own tokens" ON public.github_tokens
    FOR SELECT USING (user_id = auth.uid());

-- Users can insert their own tokens
CREATE POLICY "Users can insert their own tokens" ON public.github_tokens
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Users can update their own tokens
CREATE POLICY "Users can update their own tokens" ON public.github_tokens
    FOR UPDATE USING (user_id = auth.uid());

-- Users can delete their own tokens
CREATE POLICY "Users can delete their own tokens" ON public.github_tokens
    FOR DELETE USING (user_id = auth.uid());

-- Service role has full access (for background workers)
CREATE POLICY "Service role can manage all tokens" ON public.github_tokens
    FOR ALL USING (auth.role() = 'service_role');

-- Create updated_at trigger
CREATE TRIGGER update_github_tokens_updated_at
    BEFORE UPDATE ON public.github_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create artifacts table for generated configs
CREATE TABLE IF NOT EXISTS public.artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES public.repositories(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL CHECK (artifact_type IN ('ci_config', 'security_report', 'performance_report', 'code_report', 'dependency_report')),
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'yaml' CHECK (format IN ('yaml', 'json', 'markdown', 'html')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_artifacts_org_id ON public.artifacts(org_id);
CREATE INDEX idx_artifacts_repository_id ON public.artifacts(repository_id);
CREATE INDEX idx_artifacts_analysis_id ON public.artifacts(analysis_id);
CREATE INDEX idx_artifacts_type ON public.artifacts(artifact_type);

-- Enable RLS on artifacts
ALTER TABLE public.artifacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view artifacts in their organizations" ON public.artifacts
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

CREATE POLICY "Users can create artifacts in their organizations" ON public.artifacts
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.organizations 
            WHERE id = org_id AND owner_id = auth.uid()
        )
    );

-- Create updated_at trigger for artifacts
CREATE TRIGGER update_artifacts_updated_at
    BEFORE UPDATE ON public.artifacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();