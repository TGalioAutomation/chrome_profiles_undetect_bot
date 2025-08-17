#!/usr/bin/env python3
"""
Quick API Test for Chrome Profiles Manager
"""

import requests
import json
import time

def test_api():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Chrome Profiles Manager - Quick API Test")
    print("=" * 50)
    
    # Test 1: Server connection
    print("1. Testing server connection...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        return
    
    # Test 2: Get system status
    print("\n2. Testing GET /api/status...")
    try:
        response = requests.get(f"{base_url}/api/status")
        data = response.json()
        if data.get('success'):
            status = data.get('status', {})
            print(f"   ✅ Status OK - Profiles: {status.get('total_profiles', 0)}, Active: {status.get('active_browsers', 0)}")
        else:
            print(f"   ❌ Status failed: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get profiles (initially empty)
    print("\n3. Testing GET /api/profiles...")
    try:
        response = requests.get(f"{base_url}/api/profiles")
        data = response.json()
        if data.get('success'):
            profiles = data.get('profiles', [])
            print(f"   ✅ Got profiles list - Count: {len(profiles)}")
        else:
            print(f"   ❌ Failed to get profiles: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Create a test profile
    print("\n4. Testing POST /api/profiles (Create Profile)...")
    profile_data = {
        "name": "quick_test_profile",
        "display_name": "Quick Test Profile",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "window_size": [1366, 768],
        "headless": False,
        "notes": "Created by quick API test"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/profiles",
            json=profile_data,
            headers={"Content-Type": "application/json"}
        )
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Profile created: {data.get('message', 'Success')}")
        else:
            print(f"   ❌ Failed to create profile: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Get specific profile
    print("\n5. Testing GET /api/profiles/quick_test_profile...")
    try:
        response = requests.get(f"{base_url}/api/profiles/quick_test_profile")
        data = response.json()
        if data.get('success'):
            profile = data.get('profile', {})
            print(f"   ✅ Got profile: {profile.get('display_name', 'Unknown')}")
        else:
            print(f"   ❌ Failed to get profile: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Update profile
    print("\n6. Testing PUT /api/profiles/quick_test_profile...")
    update_data = {
        "display_name": "Updated Quick Test Profile",
        "notes": "Updated by quick API test"
    }
    
    try:
        response = requests.put(
            f"{base_url}/api/profiles/quick_test_profile",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Profile updated: {data.get('message', 'Success')}")
        else:
            print(f"   ❌ Failed to update profile: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: Start browser (this might take time)
    print("\n7. Testing POST /api/profiles/quick_test_profile/start...")
    try:
        response = requests.post(f"{base_url}/api/profiles/quick_test_profile/start")
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Browser start initiated: {data.get('message', 'Success')}")
            print("   ⏳ Waiting 5 seconds for browser to start...")
            time.sleep(5)
        else:
            print(f"   ❌ Failed to start browser: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 8: Navigate browser
    print("\n8. Testing POST /api/profiles/quick_test_profile/navigate...")
    navigate_data = {"url": "https://httpbin.org/user-agent"}
    
    try:
        response = requests.post(
            f"{base_url}/api/profiles/quick_test_profile/navigate",
            json=navigate_data,
            headers={"Content-Type": "application/json"}
        )
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Navigation successful: {data.get('message', 'Success')}")
            print("   ⏳ Waiting 3 seconds for navigation...")
            time.sleep(3)
        else:
            print(f"   ❌ Failed to navigate: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 9: Stop browser
    print("\n9. Testing POST /api/profiles/quick_test_profile/stop...")
    try:
        response = requests.post(f"{base_url}/api/profiles/quick_test_profile/stop")
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Browser stopped: {data.get('message', 'Success')}")
            print("   ⏳ Waiting 2 seconds for cleanup...")
            time.sleep(2)
        else:
            print(f"   ❌ Failed to stop browser: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 10: Delete profile
    print("\n10. Testing DELETE /api/profiles/quick_test_profile...")
    try:
        response = requests.delete(f"{base_url}/api/profiles/quick_test_profile")
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Profile deleted: {data.get('message', 'Success')}")
        else:
            print(f"   ❌ Failed to delete profile: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 11: Error handling - Get non-existent profile
    print("\n11. Testing error handling (GET non-existent profile)...")
    try:
        response = requests.get(f"{base_url}/api/profiles/non_existent_profile")
        if response.status_code == 404:
            print("   ✅ Correctly returned 404 for non-existent profile")
        else:
            print(f"   ❌ Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Test Complete!")
    print("Check the results above to see which endpoints are working.")
    print("=" * 50)

if __name__ == "__main__":
    test_api()
