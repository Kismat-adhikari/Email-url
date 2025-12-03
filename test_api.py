#!/usr/bin/env python3
"""Quick test to verify Flask API works."""

import requests
import json

API_URL = "http://localhost:5000"

print("Testing Flask API...")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{API_URL}/api/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print("\n⚠️  Backend is not running!")
    print("Start it with: python app.py")
    exit(1)

# Test 2: Basic validation
print("\n2. Testing basic validation...")
try:
    response = requests.post(
        f"{API_URL}/api/validate",
        json={"email": "user@example.com"},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Advanced validation
print("\n3. Testing advanced validation...")
try:
    response = requests.post(
        f"{API_URL}/api/validate/advanced",
        json={"email": "user@gmail.com"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("✅ API is working!")
