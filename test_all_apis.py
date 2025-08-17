#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Chrome Profiles Manager

This script tests all API endpoints to ensure they work correctly.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List


class APITester:
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_profile_name = "api_test_profile"
        self.results = []
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        if data and not success:
            print(f"    Data: {data}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        })
        print()
    
    def test_server_connection(self):
        """Test if server is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test("Server Connection", True, "Server is running")
                return True
            else:
                self.log_test("Server Connection", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connection", False, f"Connection error: {e}")
            return False
    
    def test_get_system_status(self):
        """Test GET /api/status"""
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                status = data.get('status', {})
                self.log_test("GET /api/status", True, 
                            f"Total profiles: {status.get('total_profiles', 0)}, "
                            f"Active browsers: {status.get('active_browsers', 0)}")
                return True
            else:
                self.log_test("GET /api/status", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("GET /api/status", False, f"Error: {e}")
            return False
    
    def test_get_profiles_empty(self):
        """Test GET /api/profiles (initially empty)"""
        try:
            response = self.session.get(f"{self.base_url}/api/profiles")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                profiles = data.get('profiles', [])
                self.log_test("GET /api/profiles (empty)", True, f"Found {len(profiles)} profiles")
                return True
            else:
                self.log_test("GET /api/profiles (empty)", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("GET /api/profiles (empty)", False, f"Error: {e}")
            return False
    
    def test_create_profile(self):
        """Test POST /api/profiles"""
        profile_data = {
            "name": self.test_profile_name,
            "display_name": "API Test Profile",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "proxy": None,
            "window_size": [1366, 768],
            "headless": False,
            "custom_options": ["--disable-web-security"],
            "notes": "Profile created by API test suite"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/profiles",
                json=profile_data,
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("POST /api/profiles", True, data.get('message', 'Profile created'))
                return True
            else:
                self.log_test("POST /api/profiles", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("POST /api/profiles", False, f"Error: {e}")
            return False
    
    def test_get_specific_profile(self):
        """Test GET /api/profiles/{name}"""
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/{self.test_profile_name}")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                profile = data.get('profile', {})
                self.log_test("GET /api/profiles/{name}", True, 
                            f"Profile: {profile.get('display_name', 'Unknown')}")
                return True
            else:
                self.log_test("GET /api/profiles/{name}", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("GET /api/profiles/{name}", False, f"Error: {e}")
            return False
    
    def test_get_profiles_with_data(self):
        """Test GET /api/profiles (with data)"""
        try:
            response = self.session.get(f"{self.base_url}/api/profiles")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                profiles = data.get('profiles', [])
                found_test_profile = any(p['name'] == self.test_profile_name for p in profiles)
                
                if found_test_profile:
                    self.log_test("GET /api/profiles (with data)", True, 
                                f"Found {len(profiles)} profiles including test profile")
                    return True
                else:
                    self.log_test("GET /api/profiles (with data)", False, 
                                "Test profile not found in list")
                    return False
            else:
                self.log_test("GET /api/profiles (with data)", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("GET /api/profiles (with data)", False, f"Error: {e}")
            return False
    
    def test_update_profile(self):
        """Test PUT /api/profiles/{name}"""
        update_data = {
            "display_name": "Updated API Test Profile",
            "notes": "Profile updated by API test suite",
            "window_size": [1920, 1080]
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/api/profiles/{self.test_profile_name}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("PUT /api/profiles/{name}", True, data.get('message', 'Profile updated'))
                return True
            else:
                self.log_test("PUT /api/profiles/{name}", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("PUT /api/profiles/{name}", False, f"Error: {e}")
            return False
    
    def test_start_browser(self):
        """Test POST /api/profiles/{name}/start"""
        try:
            response = self.session.post(f"{self.base_url}/api/profiles/{self.test_profile_name}/start")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("POST /api/profiles/{name}/start", True, 
                            data.get('message', 'Browser start initiated'))
                # Wait a bit for browser to start
                time.sleep(3)
                return True
            else:
                self.log_test("POST /api/profiles/{name}/start", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("POST /api/profiles/{name}/start", False, f"Error: {e}")
            return False
    
    def test_navigate_browser(self):
        """Test POST /api/profiles/{name}/navigate"""
        navigate_data = {
            "url": "https://httpbin.org/user-agent"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/profiles/{self.test_profile_name}/navigate",
                json=navigate_data,
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("POST /api/profiles/{name}/navigate", True, 
                            data.get('message', 'Navigation successful'))
                # Wait for navigation
                time.sleep(2)
                return True
            else:
                self.log_test("POST /api/profiles/{name}/navigate", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("POST /api/profiles/{name}/navigate", False, f"Error: {e}")
            return False
    
    def test_stop_browser(self):
        """Test POST /api/profiles/{name}/stop"""
        try:
            response = self.session.post(f"{self.base_url}/api/profiles/{self.test_profile_name}/stop")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("POST /api/profiles/{name}/stop", True, 
                            data.get('message', 'Browser stopped'))
                # Wait for browser to stop
                time.sleep(2)
                return True
            else:
                self.log_test("POST /api/profiles/{name}/stop", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("POST /api/profiles/{name}/stop", False, f"Error: {e}")
            return False
    
    def test_delete_profile(self):
        """Test DELETE /api/profiles/{name}"""
        try:
            response = self.session.delete(f"{self.base_url}/api/profiles/{self.test_profile_name}")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("DELETE /api/profiles/{name}", True, 
                            data.get('message', 'Profile deleted'))
                return True
            else:
                self.log_test("DELETE /api/profiles/{name}", False, f"Response: {data}")
                return False
        except Exception as e:
            self.log_test("DELETE /api/profiles/{name}", False, f"Error: {e}")
            return False
    
    def test_error_cases(self):
        """Test error handling"""
        print("🧪 Testing Error Cases:")
        
        # Test get non-existent profile
        try:
            response = self.session.get(f"{self.base_url}/api/profiles/non_existent_profile")
            if response.status_code == 404:
                self.log_test("GET non-existent profile", True, "Correctly returned 404")
            else:
                self.log_test("GET non-existent profile", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET non-existent profile", False, f"Error: {e}")
        
        # Test create profile with invalid data
        try:
            invalid_data = {"name": ""}  # Empty name
            response = self.session.post(
                f"{self.base_url}/api/profiles",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code >= 400:
                self.log_test("POST invalid profile data", True, "Correctly rejected invalid data")
            else:
                self.log_test("POST invalid profile data", False, "Should have rejected invalid data")
        except Exception as e:
            self.log_test("POST invalid profile data", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("=" * 60)
        print("🧪 Chrome Profiles Manager - API Test Suite")
        print("=" * 60)
        print()
        
        # Test sequence
        tests = [
            ("Server Connection", self.test_server_connection),
            ("System Status", self.test_get_system_status),
            ("Get Profiles (Empty)", self.test_get_profiles_empty),
            ("Create Profile", self.test_create_profile),
            ("Get Specific Profile", self.test_get_specific_profile),
            ("Get Profiles (With Data)", self.test_get_profiles_with_data),
            ("Update Profile", self.test_update_profile),
            ("Start Browser", self.test_start_browser),
            ("Navigate Browser", self.test_navigate_browser),
            ("Stop Browser", self.test_stop_browser),
            ("Delete Profile", self.test_delete_profile),
        ]
        
        # Run main tests
        for test_name, test_func in tests:
            print(f"🔄 Running: {test_name}")
            success = test_func()
            if not success:
                print(f"⚠️  Test failed: {test_name}")
                # Continue with other tests
        
        # Run error case tests
        self.test_error_cases()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        if failed_tests == 0:
            print("🎉 All tests passed! API is working correctly.")
        else:
            print(f"⚠️  {failed_tests} test(s) failed. Please check the issues above.")


def main():
    """Main function"""
    print("Starting API tests...")
    print("Make sure the Chrome Profiles Manager server is running at http://127.0.0.1:5000")
    print()
    
    # Wait for user confirmation
    input("Press Enter to start testing...")
    print()
    
    # Run tests
    tester = APITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
