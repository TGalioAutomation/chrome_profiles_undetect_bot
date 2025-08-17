#!/usr/bin/env python3
"""
Test script to debug profile creation API
"""

import requests
import json

def test_create_profile():
    url = "http://127.0.0.1:5000/api/profiles"
    
    # Test data
    profile_data = {
        "name": "debug_test_profile",
        "display_name": "Debug Test Profile",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "proxy": None,
        "window_size": [1366, 768],
        "headless": False,
        "custom_options": [],
        "notes": "Created by debug test script"
    }
    
    print("Testing profile creation API...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(profile_data, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=profile_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_create_profile()
