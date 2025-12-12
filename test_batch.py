#!/usr/bin/env python3
import requests

# Test batch endpoint with proper headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer invalid_token_for_testing",
    "X-User-ID": "test-user-123"
}

data = {
    "emails": ["test@test.com"],
    "advanced": True
}

response = requests.post(
    "http://localhost:5000/api/validate/batch/stream",
    json=data,
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")