#!/usr/bin/env python3
"""
Test script to debug profile import functionality
"""

import requests
import json
import os

def test_system_profiles():
    """Test system profiles detection"""
    print("🔍 Testing system profiles detection...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/api/system-profiles")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Count: {data.get('count', 0)}")
            
            if data['profiles']:
                print("\nFound profiles:")
                for i, profile in enumerate(data['profiles']):
                    print(f"  {i+1}. {profile['display_name']}")
                    print(f"     Path: {profile['path']}")
                    print(f"     Size: {profile['size_mb']} MB")
                    print(f"     Account: {profile['account_info'].get('email', 'N/A')}")
                    print()
            else:
                print("No profiles found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_import_profile():
    """Test profile import with manual path"""
    print("\n🔍 Testing profile import...")
    
    # Common Chrome profile paths
    test_paths = [
        os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default"),
        os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1"),
        "C:\\Users\\Public\\Desktop\\test_profile"  # Test with non-existent path
    ]
    
    for path in test_paths:
        print(f"\nTesting path: {path}")
        print(f"Exists: {os.path.exists(path)}")
        
        if os.path.exists(path):
            # Test import
            profile_data = {
                "source_path": path,
                "profile_name": "test_imported_profile",
                "display_name": "Test Imported Profile"
            }
            
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/api/import-profile",
                    json=profile_data,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Import status: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    print("✅ Import successful!")
                    break
                else:
                    print("❌ Import failed")
                    
            except Exception as e:
                print(f"Exception during import: {e}")

def test_profiles_list():
    """Test profiles list after import"""
    print("\n🔍 Testing profiles list...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/api/profiles")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total profiles: {len(data.get('profiles', []))}")
            
            for profile in data.get('profiles', []):
                print(f"- {profile['name']}: {profile['display_name']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    print("🧪 Chrome Profile Import Debug Test")
    print("=" * 50)
    
    # Test 1: System profiles detection
    test_system_profiles()
    
    # Test 2: Profile import
    test_import_profile()
    
    # Test 3: Profiles list
    test_profiles_list()
    
    print("\n✅ Debug test completed!")

if __name__ == "__main__":
    main()
