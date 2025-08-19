#!/usr/bin/env python3
"""
Debug script for import profile issue
"""

import requests
import json
import os

def test_import_profile():
    """Test import profile with specific path"""
    
    # Test path
    test_path = r"C:\Users\svphu\AppData\Local\Google\Chrome\User Data\Profile 2"
    
    print(f"🔍 Testing import with path: {test_path}")
    print(f"📁 Path exists: {os.path.exists(test_path)}")
    print(f"📁 Is directory: {os.path.isdir(test_path)}")
    
    if os.path.exists(test_path):
        print(f"📊 Directory contents:")
        try:
            contents = os.listdir(test_path)
            for item in contents[:10]:  # Show first 10 items
                item_path = os.path.join(test_path, item)
                print(f"  - {item} ({'dir' if os.path.isdir(item_path) else 'file'})")
            if len(contents) > 10:
                print(f"  ... and {len(contents) - 10} more items")
        except Exception as e:
            print(f"❌ Error reading directory: {e}")
    
    # Test API call
    print(f"\n🚀 Testing API import...")
    
    data = {
        "source_path": test_path,
        "profile_name": "test_profile_debug",
        "display_name": "Test Profile Debug"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/import-profile",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")

def test_system_profiles():
    """Test system profiles detection"""
    print(f"\n🔍 Testing system profiles detection...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/api/system-profiles")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Found {len(data.get('profiles', []))} profiles")
            
            for profile in data.get('profiles', []):
                print(f"  - {profile['name']}: {profile['path']}")
                if 'Profile 2' in profile['path']:
                    print(f"    ✅ Found target profile!")
                    print(f"    📊 Details: {profile}")
        else:
            print(f"❌ API error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    print("🧪 Import Profile Debug Test")
    print("=" * 50)
    
    test_system_profiles()
    test_import_profile()
    
    print("\n✅ Debug test completed!")
