#!/usr/bin/env python3
"""
Gmail Inbox Checker Script
Checks Gmail inbox and returns unread count
"""

def run_script(driver, profile_name, **kwargs):
    """
    Main script function
    
    Args:
        driver: Selenium WebDriver instance
        profile_name: Name of the Chrome profile
        **kwargs: Additional parameters
    
    Returns:
        dict: Script result
    """
    try:
        print(f"🔍 Checking Gmail for profile: {profile_name}")
        
        # Navigate to Gmail
        driver.get("https://mail.google.com/mail/u/0/#inbox")
        time.sleep(5)
        
        # Check if logged in
        if "accounts.google.com" in driver.current_url:
            return {
                "success": False,
                "message": "Not logged into Gmail",
                "data": {"logged_in": False}
            }
        
        # Get unread count
        try:
            unread_elements = driver.find_elements("css selector", "tr.zE")
            unread_count = len(unread_elements)
            
            return {
                "success": True,
                "message": f"Found {unread_count} unread emails",
                "data": {
                    "unread_count": unread_count,
                    "logged_in": True,
                    "inbox_url": driver.current_url
                }
            }
        except Exception as e:
            return {
                "success": True,
                "message": "Gmail accessible but couldn't count emails",
                "data": {
                    "logged_in": True,
                    "error": str(e)
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Script error: {str(e)}",
            "data": {"error": str(e)}
        }
