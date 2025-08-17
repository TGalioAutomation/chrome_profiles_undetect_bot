#!/usr/bin/env python3
"""
Test script to simulate web UI request
"""

import requests
import json

def test_web_ui_request():
    """Simulate the exact request from web UI"""
    url = "http://127.0.0.1:5000/api/profiles"
    
    # Simulate form data from web UI
    profile_data = {
        "name": "web_ui_test",
        "display_name": "Web UI Test",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "proxy": "",  # Empty string like from form
        "window_size": [1366, 768],
        "headless": False,
        "custom_options": [],
        "notes": ""
    }
    
    print("🧪 Testing Web UI Profile Creation")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Data: {json.dumps(profile_data, indent=2)}")
    print()
    
    try:
        # Simulate browser request
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "http://127.0.0.1:5000/profiles"
        }
        
        response = requests.post(url, json=profile_data, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Text: {response.text}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data}")
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw error: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_empty_request():
    """Test with empty/invalid data"""
    url = "http://127.0.0.1:5000/api/profiles"
    
    print("\n🧪 Testing Empty Request")
    print("=" * 50)
    
    try:
        # Test with empty body
        response = requests.post(url, json={}, headers={"Content-Type": "application/json"})
        print(f"Empty JSON - Status: {response.status_code}, Response: {response.text}")
        
        # Test with None
        response = requests.post(url, json=None, headers={"Content-Type": "application/json"})
        print(f"None JSON - Status: {response.status_code}, Response: {response.text}")
        
        # Test with invalid JSON
        response = requests.post(url, data="invalid json", headers={"Content-Type": "application/json"})
        print(f"Invalid JSON - Status: {response.status_code}, Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_web_ui_request()
    test_empty_request()
