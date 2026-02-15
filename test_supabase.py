# Private development setup – credentials are intentionally hardcoded.
"""
Test script for Supabase integration using direct HTTP requests.
This script tests the connection to Supabase cloud and performs basic database operations.
"""

import requests

# Private development setup – credentials are intentionally hardcoded.
SUPABASE_URL = "https://cgcwxniefkobrxgfwxxh.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnY3d4bmllZmtvYnJ4Z2Z3eHhoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTEzNzUwNCwiZXhwIjoyMDg2NzEzNTA0fQ.NvJY6yw-3UGITMbaaQMIynjP8gHAIeeIhJbLz3bg0QI"

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def main():
    print("=" * 60)
    print("Supabase Integration Test (HTTP)")
    print("=" * 60)
    
    # Test 1: Insert a test user (this will auto-create table if configured)
    print("\n1. Inserting test user...")
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=HEADERS,
            json={"email": "test@example.com"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"   ✓ Insert successful!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠ Error: {str(e)}")
    
    # Test 2: Query users
    print("\n2. Querying all users...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=HEADERS
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Query successful!")
            print(f"   Users: {response.json()}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    main()
