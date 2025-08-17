#!/usr/bin/env python3
"""
Simple import test
"""

import requests
import json

def test_import():
    url = "http://127.0.0.1:5000/api/import-profile"
    
    data = {
        "source_path": "C:\\Users\\svphu\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1",
        "profile_name": "test_import_simple",
        "display_name": "Test Import Simple"
    }
    
    print(f"Testing import with data: {data}")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_import()
