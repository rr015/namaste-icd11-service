# test_env.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Environment Variables Check:")
print(f"WHO_ICD_CLIENT_ID: {os.getenv('WHO_ICD_CLIENT_ID', 'NOT FOUND')}")
print(f"WHO_ICD_CLIENT_SECRET: {'*' * 10 if os.getenv('WHO_ICD_CLIENT_SECRET') else 'NOT FOUND'}")
print(f"SECRET_KEY: {os.getenv('SECRET_KEY', 'NOT FOUND')}")

# Test if .env file is being read
env_path = '.env'
if os.path.exists(env_path):
    print(f"✅ .env file found at: {env_path}")
    with open(env_path, 'r') as f:
        content = f.read()
        print("📄 .env file content:")
        print(content)
else:
    print("❌ .env file not found!")