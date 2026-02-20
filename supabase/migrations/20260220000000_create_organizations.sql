-- Create organizations table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create index on owner_id
CREATE INDEX idx_organizations_owner_id ON public.organizations(owner_id);

-- Create index on github_id
CREATE INDEX idx_organizations_github_id ON public.organizations(github_id);

-- Enable Row Level Security
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view organizations they own or are members of
CREATE POLICY "Users can view their organizations" ON public.organizations
    FOR SELECT USING (
        owner_id = auth.uid() OR 
        EXISTS (
            SELECT 1 FROM public.organization_members 
            WHERE org_id = id AND user_id = auth.uid()
        )
    );

-- Policy: Only owner can update organization
CREATE POLICY "Only owner can update organization" ON public.organizations
    FOR UPDATE USING (owner_id = auth.uid());

-- Policy: Users can create organizations
CREATE POLICY "Users can create organizations" ON public.organizations
    FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();