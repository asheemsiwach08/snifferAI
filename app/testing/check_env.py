#!/usr/bin/env python3
"""
Script to check environment variables and OpenAI connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔧 Environment Variables Check:")
print("=" * 50)

# Check OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
if openai_key:
    print(f"  Key preview: {openai_key[:20]}...")

# Check Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_table = os.getenv("SUPABASE_TABLE")

print(f"Supabase URL: {'✅ Set' if supabase_url else '❌ Not set'}")
print(f"Supabase Key: {'✅ Set' if supabase_key else '❌ Not set'}")
print(f"Supabase Table: {'✅ Set' if supabase_table else '❌ Not set'}")

if supabase_url:
    print(f"  URL: {supabase_url}")
if supabase_key:
    print(f"  Key preview: {supabase_key[:20]}...")

print("\n🔍 Checking .env file:")
print("=" * 30)

# Check if .env file exists
env_file_path = ".env"
if os.path.exists(env_file_path):
    print(f"✅ .env file found at: {os.path.abspath(env_file_path)}")
    
    # Read and show .env content (without showing full keys)
    with open(env_file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'KEY' in key.upper() and value:
                        print(f"  {key}=***{value[-4:] if len(value) > 4 else '***'}")
                    else:
                        print(f"  {key}={value}")
else:
    print(f"❌ .env file not found at: {os.path.abspath(env_file_path)}")

print("\n💡 Troubleshooting:")
print("=" * 20)

if not openai_key:
    print("1. Create a .env file in the SniffrAI directory")
    print("2. Add your OpenAI API key:")
    print("   OPENAI_API_KEY=your_api_key_here")
    print("3. Get your API key from: https://platform.openai.com/api-keys")

if not all([supabase_url, supabase_key, supabase_table]):
    print("4. Add your Supabase credentials to .env:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_KEY=your_supabase_anon_key")
    print("   SUPABASE_TABLE=lenders_data")

print("\n5. Make sure to restart your Python script after creating/updating .env") 