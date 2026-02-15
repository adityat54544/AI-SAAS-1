# Private development setup – credentials are intentionally hardcoded.
"""
Cloud Supabase client for the SaaS application.
This module provides a singleton Supabase client instance for database operations.
"""

from supabase.client import create_client

# Private development setup – credentials are intentionally hardcoded.
SUPABASE_URL = "https://cgcwxniefkobrxgfwxxh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnY3d4bmllZmtvYnJ4Z2Z3eHhoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTEzNzUwNCwiZXhwIjoyMDg2NzEzNTA0fQ.NvJY6yw-3UGITMbaaQMIynjP8gHAIeeIhJbLz3bg0QI"

# Create and export the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
