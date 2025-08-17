#!/usr/bin/env python3
"""
Example test script for Chrome Profiles Manager

This script demonstrates how to use the Chrome Profiles Manager
to create profiles and control browsers programmatically.
"""

import time
import asyncio
from core.profile_manager import ProfileManager, ChromeProfile, ProfileStatus
from core.chrome_driver import ChromeDriverManager
from core.bot_bypass import BotBypassManager


def test_profile_management():
    """Test profile creation and management"""
    print("🧪 Testing Profile Management...")
    
    # Initialize profile manager
    pm = ProfileManager()
    
    # Create a test profile
    test_profile = ChromeProfile(
        name="test_profile_1",
        display_name="Test Profile 1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        proxy=None,
        window_size=(1366, 768),
        headless=False,
        notes="Test profile for demonstration"
    )
    
    # Create profile
    success = pm.create_profile(test_profile)
    print(f"✅ Profile created: {success}")
    
    # List profiles
    profiles = pm.list_profiles()
    print(f"📋 Total profiles: {len(profiles)}")
    
    # Get specific profile
    profile = pm.get_profile("test_profile_1")
    if profile:
        print(f"🔍 Found profile: {profile.display_name}")
    
    # Update profile
    pm.update_profile("test_profile_1", {"notes": "Updated test profile"})
    print("✏️ Profile updated")
    
    return "test_profile_1"


def test_browser_automation(profile_name):
    """Test browser automation with bot bypass"""
    print(f"\n🤖 Testing Browser Automation for profile: {profile_name}")
    
    try:
        # Create driver manager
        driver_manager = ChromeDriverManager(profile_name)
        
        # Start browser
        print("🚀 Starting browser...")
        driver = driver_manager.start_driver(
            headless=False,
            window_size=(1366, 768)
        )
        
        # Apply bot bypass techniques
        print("🛡️ Applying bot bypass techniques...")
        bypass_manager = BotBypassManager(driver)
        bypass_manager.apply_all_bypasses()
        
        # Navigate to test page
        print("🌐 Navigating to test page...")
        driver_manager.navigate_to("https://bot.sannysoft.com/")
        
        # Wait for page to load
        time.sleep(5)
        
        # Take a screenshot (optional)
        try:
            driver.save_screenshot(f"screenshots/test_{profile_name}.png")
            print("📸 Screenshot saved")
        except:
            print("⚠️ Could not save screenshot")
        
        # Test human-like behavior
        print("👤 Testing human-like behavior...")
        
        # Random scroll
        driver_manager._random_scroll()
        time.sleep(2)
        
        # Navigate to another page
        print("🔗 Navigating to another page...")
        driver_manager.navigate_to("https://httpbin.org/headers")
        time.sleep(3)
        
        # Check if we can find the user agent in the response
        try:
            page_source = driver.page_source
            if "Chrome" in page_source:
                print("✅ User agent successfully spoofed")
            else:
                print("⚠️ User agent might not be working correctly")
        except:
            print("⚠️ Could not check user agent")
        
        print("✅ Browser automation test completed successfully!")
        
        # Keep browser open for manual inspection
        input("\n⏸️ Press Enter to close the browser...")
        
    except Exception as e:
        print(f"❌ Error during browser automation: {e}")
        
    finally:
        # Clean up
        try:
            driver_manager.quit_driver()
            print("🧹 Browser closed")
        except:
            pass


def test_api_simulation():
    """Simulate API calls"""
    print("\n🔌 Testing API Simulation...")
    
    pm = ProfileManager()
    
    # Simulate starting a session
    session_id = pm.start_session("test_profile_1")
    print(f"🎬 Session started: {session_id}")
    
    # Simulate some activity
    time.sleep(2)
    
    # End session
    pm.end_session(session_id, pages_visited=3)
    print("🎬 Session ended")
    
    # Get active profiles
    active_profiles = pm.get_active_profiles()
    print(f"🏃 Active profiles: {len(active_profiles)}")


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    pm = ProfileManager()
    
    # Delete test profile
    success = pm.delete_profile("test_profile_1", delete_files=True)
    print(f"🗑️ Test profile deleted: {success}")


def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Chrome Profiles Manager - Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Profile Management
        profile_name = test_profile_management()
        
        # Test 2: Browser Automation (optional - requires user interaction)
        choice = input("\n❓ Do you want to test browser automation? (y/n): ").lower()
        if choice == 'y':
            test_browser_automation(profile_name)
        
        # Test 3: API Simulation
        test_api_simulation()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        
    finally:
        # Cleanup
        cleanup_choice = input("\n❓ Do you want to clean up test data? (y/n): ").lower()
        if cleanup_choice == 'y':
            cleanup_test_data()
        
        print("\n👋 Test suite finished!")


if __name__ == "__main__":
    main()
