#!/usr/bin/env python3
"""
Selenium Script Manager
Handles execution of custom Selenium scripts on Chrome profiles
"""

import os
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import importlib.util
import sys

# Script storage directory
SCRIPTS_DIR = Path("scripts")
SCRIPTS_DIR.mkdir(exist_ok=True)

@dataclass
class ScriptResult:
    """Result of script execution"""
    success: bool
    message: str
    data: Any = None
    error: str = None
    execution_time: float = 0
    timestamp: str = None

@dataclass
class SeleniumScript:
    """Selenium script metadata"""
    name: str
    display_name: str
    description: str
    file_path: str
    parameters: List[Dict[str, Any]] = None
    created_at: str = None
    last_run: str = None
    run_count: int = 0

class SeleniumScriptManager:
    """Manager for Selenium scripts"""
    
    def __init__(self):
        self.scripts_dir = SCRIPTS_DIR
        self.scripts_dir.mkdir(exist_ok=True)
        
        # Create examples directory
        examples_dir = self.scripts_dir / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        # Create default example scripts
        self._create_example_scripts()
    
    def _create_example_scripts(self):
        """Create example scripts for users"""
        examples = [
            {
                "name": "gmail_checker.py",
                "content": '''#!/usr/bin/env python3
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
'''
            },
            {
                "name": "page_screenshot.py", 
                "content": '''#!/usr/bin/env python3
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
'''
            }
        ]
        
        for example in examples:
            example_path = self.scripts_dir / "examples" / example["name"]
            if not example_path.exists():
                with open(example_path, 'w', encoding='utf-8') as f:
                    f.write(example["content"])
    
    def list_scripts(self) -> List[SeleniumScript]:
        """List all available scripts"""
        scripts = []
        
        for script_file in self.scripts_dir.rglob("*.py"):
            if script_file.name.startswith("__"):
                continue
                
            try:
                script_info = self._get_script_info(script_file)
                if script_info:
                    scripts.append(script_info)
            except Exception as e:
                print(f"Error reading script {script_file}: {e}")
        
        return scripts
    
    def _get_script_info(self, script_path: Path) -> Optional[SeleniumScript]:
        """Get script information from file"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract docstring for description
            description = "No description available"
            if '"""' in content:
                start = content.find('"""') + 3
                end = content.find('"""', start)
                if end > start:
                    description = content[start:end].strip()
            
            return SeleniumScript(
                name=script_path.name,
                display_name=script_path.stem.replace('_', ' ').title(),
                description=description,
                file_path=str(script_path),
                created_at=datetime.fromtimestamp(script_path.stat().st_ctime).isoformat()
            )
            
        except Exception as e:
            print(f"Error getting script info: {e}")
            return None
    
    def execute_script(self, script_name: str, driver, profile_name: str, **kwargs) -> ScriptResult:
        """Execute a Selenium script"""
        start_time = time.time()
        
        try:
            # Find script file
            script_path = None
            for script_file in self.scripts_dir.rglob(script_name):
                if script_file.is_file():
                    script_path = script_file
                    break
            
            if not script_path:
                return ScriptResult(
                    success=False,
                    message=f"Script not found: {script_name}",
                    error="Script file not found",
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now().isoformat()
                )
            
            # Load and execute script
            spec = importlib.util.spec_from_file_location("script_module", script_path)
            script_module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to handle imports
            sys.modules["script_module"] = script_module
            spec.loader.exec_module(script_module)
            
            # Execute script
            if hasattr(script_module, 'run_script'):
                result = script_module.run_script(driver, profile_name, **kwargs)
                
                execution_time = time.time() - start_time
                
                return ScriptResult(
                    success=result.get('success', True),
                    message=result.get('message', 'Script executed'),
                    data=result.get('data'),
                    error=result.get('error'),
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return ScriptResult(
                    success=False,
                    message="Script missing run_script function",
                    error="No run_script function found",
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            return ScriptResult(
                success=False,
                message=f"Script execution failed: {str(e)}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time,
                timestamp=datetime.now().isoformat()
            )
        finally:
            # Clean up module
            if "script_module" in sys.modules:
                del sys.modules["script_module"]
