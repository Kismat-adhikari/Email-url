#!/usr/bin/env python3
"""
Test team API performance improvements
"""

import time
import requests
import json

def test_team_api_performance():
    """Test the performance of team API endpoints"""
    
    base_url = "http://localhost:3000"
    
    # You'll need to get a valid token from your app
    # For now, this is just a template
    token = "your_jwt_token_here"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🚀 Testing Team API Performance")
    print("=" * 50)
    
    # Test 1: Old method (two separate calls)
    print("\n📊 Test 1: Old Method (Separate API calls)")
    start_time = time.time()
    
    try:
        # Simulate old method: eligibility check + team info
        eligibility_response = requests.get(f"{base_url}/api/team/check-eligibility", headers=headers, timeout=5)
        if eligibility_response.status_code == 200:
            team_response = requests.get(f"{base_url}/api/team/info", headers=headers, timeout=5)
        
        old_method_time = time.time() - start_time
        print(f"   ⏱️  Time: {old_method_time:.3f} seconds")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        old_method_time = float('inf')
    
    # Test 2: New optimized method (single call)
    print("\n📊 Test 2: New Optimized Method (Single API call)")
    start_time = time.time()
    
    try:
        status_response = requests.get(f"{base_url}/api/team/status", headers=headers, timeout=5)
        new_method_time = time.time() - start_time
        print(f"   ⏱️  Time: {new_method_time:.3f} seconds")
        
        if status_response.status_code == 200:
            data = status_response.json()
            print(f"   ✅ Success: Got team status")
            print(f"   📋 Can create team: {data.get('can_create_team', 'N/A')}")
            print(f"   👥 In team: {data.get('in_team', 'N/A')}")
        else:
            print(f"   ❌ HTTP {status_response.status_code}: {status_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        new_method_time = float('inf')
    
    # Performance comparison
    print("\n🏆 Performance Comparison")
    print("=" * 30)
    
    if old_method_time != float('inf') and new_method_time != float('inf'):
        improvement = ((old_method_time - new_method_time) / old_method_time) * 100
        print(f"Old method: {old_method_time:.3f}s")
        print(f"New method: {new_method_time:.3f}s")
        print(f"Improvement: {improvement:.1f}% faster")
        
        if improvement > 0:
            print("✅ Performance improved!")
        else:
            print("⚠️  Performance needs more work")
    else:
        print("❌ Could not complete performance test")
        print("💡 Make sure your backend is running and you have a valid token")
    
    print("\n📝 Optimization Summary:")
    print("   • Combined two API calls into one")
    print("   • Reduced database queries")
    print("   • Added loading skeleton for better UX")
    print("   • Reduced auto-refresh from 10s to 30s")
    print("   • Optimized team member queries")

if __name__ == "__main__":
    print("🔧 Team Performance Test")
    print("Note: Update the token variable with a valid JWT token to run the test")
    test_team_api_performance()