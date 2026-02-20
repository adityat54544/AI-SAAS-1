-- Create jobs table
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL CHECK (job_type IN ('analysis', 'clone', 'sync', 'ci_generation')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    repository_id UUID REFERENCES public.repositories(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    payload JSONB,
    result_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_jobs_repository_id ON public.jobs(repository_id);
CREATE INDEX idx_jobs_status ON public.jobs(status);
CREATE INDEX idx_jobs_job_type ON public.jobs(job_type);
CREATE INDEX idx_jobs_created_at ON public.jobs(created_at DESC);

-- Enable Row Level Security
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view jobs for accessible repositories
CREATE POLICY "Users can view jobs for accessible repositories" ON public.jobs
    FOR SELECT USING (
        repository_id IS NULL OR EXISTS (
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

-- Policy: Service role can manage all jobs (for worker processes)
CREATE POLICY "Service role can manage all jobs" ON public.jobs
    FOR ALL USING (auth.role() = 'service_role');

-- Create updated_at trigger
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON public.jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create job_logs table for detailed logging
CREATE TABLE IF NOT EXISTS public.job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    level TEXT NOT NULL DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warning', 'error')),
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_job_logs_job_id ON public.job_logs(job_id);
CREATE INDEX idx_job_logs_created_at ON public.job_logs(created_at DESC);

-- Enable RLS on job_logs
ALTER TABLE public.job_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view logs for accessible jobs" ON public.job_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.jobs j
            WHERE j.id = job_id AND (
                j.repository_id IS NULL OR EXISTS (
                    SELECT 1 FROM public.repositories r
                    JOIN public.organizations o ON o.id = r.org_id
                    WHERE r.id = j.repository_id AND (
                        o.owner_id = auth.uid() OR 
                        EXISTS (
                            SELECT 1 FROM public.organization_members 
                            WHERE org_id = o.id AND user_id = auth.uid()
                        )
                    )
                )
            )
        )
    );