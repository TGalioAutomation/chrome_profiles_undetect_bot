#!/usr/bin/env python3
"""
Test Chrome driver Gmail access
"""

import requests
import json
import time

def test_profile_start_and_gmail():
    """Test starting profile and Gmail access"""
    
    # First, get list of profiles
    print("🔍 Getting profiles list...")
    response = requests.get("http://127.0.0.1:5000/api/profiles")
    
    if response.status_code != 200:
        print(f"❌ Failed to get profiles: {response.text}")
        return
    
    data = response.json()
    if not data['success'] or not data['profiles']:
        print("❌ No profiles found")
        return
    
    # Find an imported profile (likely has Gmail login)
    imported_profiles = [p for p in data['profiles'] if 'imported' in p.get('notes', '').lower()]
    
    if not imported_profiles:
        print("⚠️ No imported profiles found, using first available profile")
        test_profile = data['profiles'][0]
    else:
        test_profile = imported_profiles[0]
    
    profile_name = test_profile['name']
    print(f"🧪 Testing profile: {profile_name}")
    print(f"   Display name: {test_profile['display_name']}")
    print(f"   Notes: {test_profile.get('notes', 'N/A')}")
    
    # Start browser
    print(f"\n🚀 Starting browser for profile: {profile_name}")
    start_response = requests.post(f"http://127.0.0.1:5000/api/profiles/{profile_name}/start")
    
    if start_response.status_code != 200:
        print(f"❌ Failed to start browser: {start_response.text}")
        return
    
    start_data = start_response.json()
    print(f"✅ Browser start response: {start_data['message']}")
    
    # Wait for browser to fully start
    print("⏳ Waiting for browser to initialize...")
    time.sleep(10)
    
    # Test Gmail access
    print(f"\n🧪 Testing Gmail access...")
    gmail_response = requests.post(f"http://127.0.0.1:5000/api/profiles/{profile_name}/test-gmail")
    
    if gmail_response.status_code == 200:
        gmail_data = gmail_response.json()
        print(f"📊 Gmail test result:")
        print(f"   Success: {gmail_data['success']}")
        print(f"   Gmail accessible: {gmail_data.get('gmail_accessible', 'Unknown')}")
        print(f"   Message: {gmail_data.get('message', 'N/A')}")
        
        if gmail_data.get('gmail_accessible'):
            print("✅ Gmail is accessible - profile working correctly!")
        else:
            print("⚠️ Gmail not accessible - may need manual login or profile issue")
    else:
        print(f"❌ Gmail test failed: {gmail_response.text}")
    
    # Navigate to Gmail manually
    print(f"\n🌐 Manually navigating to Gmail...")
    nav_response = requests.post(
        f"http://127.0.0.1:5000/api/profiles/{profile_name}/navigate",
        json={"url": "https://mail.google.com"}
    )
    
    if nav_response.status_code == 200:
        nav_data = nav_response.json()
        print(f"✅ Navigation response: {nav_data['message']}")
    else:
        print(f"❌ Navigation failed: {nav_response.text}")
    
    print(f"\n📋 Test completed for profile: {profile_name}")
    print("💡 Check the browser window to see if Gmail is accessible")
    
    # Keep browser open for manual inspection
    input("\n⏸️ Press Enter to stop the browser...")
    
    # Stop browser
    stop_response = requests.post(f"http://127.0.0.1:5000/api/profiles/{profile_name}/stop")
    if stop_response.status_code == 200:
        print("✅ Browser stopped")
    else:
        print(f"⚠️ Failed to stop browser: {stop_response.text}")

def main():
    print("🧪 Chrome Driver Gmail Test")
    print("=" * 50)
    
    try:
        test_profile_start_and_gmail()
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
