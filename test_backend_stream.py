#!/usr/bin/env python3
"""Test the streaming endpoint directly"""
import requests
import json
import uuid

# Generate a test UUID
test_uuid = str(uuid.uuid4())

url = 'http://localhost:5000/api/validate/batch/stream'
headers = {
    'Content-Type': 'application/json',
    'X-User-ID': test_uuid
}
data = {
    'emails': ['test@gmail.com', 'user@yahoo.com'],
    'advanced': True
}

print(f"Testing streaming endpoint with UUID: {test_uuid}")
print(f"URL: {url}")
print(f"Data: {data}\n")

response = requests.post(url, headers=headers, json=data, stream=True)

print(f"Status Code: {response.status_code}\n")

if response.status_code == 200:
    print("Streaming response:")
    print("-" * 80)
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                data_str = decoded[6:]
                try:
                    data_obj = json.loads(data_str)
                    print(json.dumps(data_obj, indent=2))
                    print("-" * 80)
                except:
                    print(decoded)
else:
    print(f"Error: {response.text}")
