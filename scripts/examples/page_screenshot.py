#!/usr/bin/env python3
"""
Page Screenshot Script
Takes screenshot of current page
"""

import os
from datetime import datetime

def run_script(driver, profile_name, **kwargs):
    """
    Take screenshot of current page
    
    Args:
        driver: Selenium WebDriver instance
        profile_name: Name of the Chrome profile
        **kwargs: Additional parameters (url, filename)
    
    Returns:
        dict: Script result
    """
    try:
        # Get parameters
        url = kwargs.get('url', driver.current_url)
        filename = kwargs.get('filename', f"screenshot_{profile_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        # Navigate to URL if provided
        if url and url != driver.current_url:
            print(f"🌐 Navigating to: {url}")
            driver.get(url)
            time.sleep(3)
        
        # Create screenshots directory
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, filename)
        driver.save_screenshot(screenshot_path)
        
        return {
            "success": True,
            "message": f"Screenshot saved: {screenshot_path}",
            "data": {
                "screenshot_path": screenshot_path,
                "url": driver.current_url,
                "page_title": driver.title
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Screenshot failed: {str(e)}",
            "data": {"error": str(e)}
        }
