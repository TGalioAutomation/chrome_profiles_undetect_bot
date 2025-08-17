#!/usr/bin/env python3
"""
Test creating a new profile with unique name
"""

import requests
import json
import time

def test_new_profile():
    url = "http://127.0.0.1:5000/api/profiles"
    
    # Use timestamp to ensure unique name
    timestamp = int(time.time())
    profile_data = {
        "name": f"test_profile_{timestamp}",
        "display_name": f"Test Profile {timestamp}",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "proxy": None,
        "window_size": [1366, 768],
        "headless": False,
        "custom_options": [],
        "notes": "Test profile with unique name"
    }
    
    print("🧪 Testing New Profile Creation")
    print("=" * 50)
    print(f"Profile name: {profile_data['name']}")
    
    try:
        response = requests.post(url, json=profile_data, headers={"Content-Type": "application/json"})
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['message']}")
        else:
            data = response.json()
            print(f"❌ Error: {data['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_new_profile()
