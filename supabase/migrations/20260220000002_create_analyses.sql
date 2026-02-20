-- Create analyses table
CREATE TABLE IF NOT EXISTS public.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    analysis_type TEXT NOT NULL DEFAULT 'full' CHECK (analysis_type IN ('full', 'security', 'performance', 'ci_cd')),
    triggered_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_analyses_repository_id ON public.analyses(repository_id);
CREATE INDEX idx_analyses_status ON public.analyses(status);
CREATE INDEX idx_analyses_triggered_by ON public.analyses(triggered_by);
CREATE INDEX idx_analyses_created_at ON public.analyses(created_at DESC);

-- Enable Row Level Security
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view analyses for accessible repositories
CREATE POLICY "Users can view analyses for accessible repositories" ON public.analyses
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

-- Policy: Users can create analyses for accessible repositories
CREATE POLICY "Users can create analyses" ON public.analyses
    FOR INSERT WITH CHECK (
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

-- Create updated_at trigger
CREATE TRIGGER update_analyses_updated_at
    BEFORE UPDATE ON public.analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create recommendations table
CREATE TABLE IF NOT EXISTS public.recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('security', 'performance', 'code_quality', 'ci_cd', 'dependencies', 'general')),
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    suggested_fix TEXT,
    is_dismissed BOOLEAN DEFAULT false,
    dismissed_by UUID REFERENCES public.users(id),
    dismissed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for recommendations
CREATE INDEX idx_recommendations_analysis_id ON public.recommendations(analysis_id);
CREATE INDEX idx_recommendations_category ON public.recommendations(category);
CREATE INDEX idx_recommendations_severity ON public.recommendations(severity);
CREATE INDEX idx_recommendations_file_path ON public.recommendations(file_path);

-- Enable RLS on recommendations
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view recommendations for accessible analyses" ON public.recommendations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.analyses a
            JOIN public.repositories r ON r.id = a.repository_id
            JOIN public.organizations o ON o.id = r.org_id
            WHERE a.id = analysis_id AND (
                o.owner_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM public.organization_members 
                    WHERE org_id = o.id AND user_id = auth.uid()
                )
            )
        )
    );

-- Create remediation_snippets table
CREATE TABLE IF NOT EXISTS public.remediation_snippets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    original_code TEXT NOT NULL,
    suggested_code TEXT NOT NULL,
    explanation TEXT,
    apply_status TEXT DEFAULT 'pending' CHECK (apply_status IN ('pending', 'applied', 'rejected')),
    applied_by UUID REFERENCES public.users(id),
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_remediation_analysis_id ON public.remediation_snippets(analysis_id);

-- Enable RLS on remediation_snippets
ALTER TABLE public.remediation_snippets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view remediation snippets for accessible analyses" ON public.remediation_snippets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.analyses a
            JOIN public.repositories r ON r.id = a.repository_id
            JOIN public.organizations o ON o.id = r.org_id
            WHERE a.id = analysis_id AND (
                o.owner_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM public.organization_members 
                    WHERE org_id = o.id AND user_id = auth.uid()
                )
            )
        )
    );