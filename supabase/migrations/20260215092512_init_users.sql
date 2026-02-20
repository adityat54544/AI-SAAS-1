-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read (optional - adjust as needed)
CREATE POLICY "Users are viewable by everyone" ON public.users
    FOR SELECT USING (true);

-- Create policy to allow insert (optional - adjust as needed)
CREATE POLICY "Users can be inserted by anyone" ON public.users
    FOR INSERT WITH CHECK (true);
