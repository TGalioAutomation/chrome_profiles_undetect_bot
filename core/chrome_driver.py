import os
import random
import time
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager as WDM
from selenium.webdriver.chrome.service import Service
from .gmail_manager import GmailManager
from .script_manager import SeleniumScriptManager
from .prompt_manager import PromptManager
from .ai_image_generator import create_generator
from .thread_manager import MultiThreadGenerator, ThreadConfig

from config import DEFAULT_CHROME_OPTIONS, USER_AGENTS, PROFILES_DIR


class ChromeDriverManager:
    """
    Advanced Chrome Driver Manager with bot detection bypass capabilities
    """
    
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.profile_path = PROFILES_DIR / profile_name
        self.driver: Optional[webdriver.Chrome] = None
        self.ua = UserAgent()
        self.gmail_manager = None
        self.script_manager = SeleniumScriptManager()
        self.prompt_manager = PromptManager()
        self.thread_id = None  # For multi-threading identification

        # Create profile directory if it doesn't exist
        self.profile_path.mkdir(exist_ok=True)
        
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from pool or generate one"""
        try:
            return random.choice(USER_AGENTS)
        except:
            return self.ua.random
    
    def _setup_chrome_options(self,
                            headless: bool = False,
                            proxy: Optional[str] = None,
                            user_agent: Optional[str] = None,
                            window_size: tuple = (1920, 1080),
                            custom_options: List[str] = None,
                            use_undetected: bool = True,
                             skip_user_data_dir: bool = False) -> Options:
        """Setup Chrome options with bot bypass configurations"""
        
        options = Options()
        
        # Add default options for bot bypass
        for option in DEFAULT_CHROME_OPTIONS:
            options.add_argument(option)
        
        # Profile settings - use imported profile structure
        if not skip_user_data_dir:
            options.add_argument(f"--user-data-dir={self.profile_path}")

            # Check if this is an imported profile (has Default subdirectory)
            default_profile_path = self.profile_path / "Default"
            if default_profile_path.exists():
                options.add_argument("--profile-directory=Default")
            else:
                # For new profiles, create Default directory structure
                default_profile_path.mkdir(exist_ok=True)
        
        # Window settings
        if headless:
            options.add_argument("--headless=new")
        options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        
        # User agent
        if not user_agent:
            user_agent = self._get_random_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        
        # Proxy settings
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        
        # Custom options
        if custom_options:
            for option in custom_options:
                options.add_argument(option)
        
        # Gmail-specific stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        options.add_argument('--use-mock-keychain')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI,VizDisplayCompositor')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')

        # Additional stealth options (only for regular webdriver, not undetected)
        if not use_undetected:
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

        # Enhanced preferences for Gmail
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 1,  # Enable images for Gmail
            "profile.default_content_setting_values.plugins": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2
        })
        
        return options
    
    def _apply_stealth_settings(self):
        """Apply additional stealth settings to bypass bot detection"""
        if not self.driver:
            return

        try:
            # Apply selenium-stealth first (this handles webdriver property)
            stealth(self.driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)

            # Additional overrides (safe property checking)
            self.driver.execute_script("""
                try {
                    // Check plugins property
                    const pluginsDescriptor = Object.getOwnPropertyDescriptor(navigator, 'plugins');
                    if (!pluginsDescriptor || pluginsDescriptor.configurable) {
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                {name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer'},
                                {name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                                {name: 'Native Client', description: '', filename: 'internal-nacl-plugin'}
                            ],
                            configurable: true
                        });
                    }
                } catch(e) {
                    console.debug('Plugin override skipped:', e.message);
                }
            """)

            self.driver.execute_script("""
                try {
                    // Check if languages property is configurable
                    const descriptor = Object.getOwnPropertyDescriptor(navigator, 'languages');
                    if (!descriptor || descriptor.configurable) {
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                            configurable: true
                        });
                    } else {
                        // Property exists and not configurable, skip override
                        console.debug('Languages property not configurable, skipping override');
                    }
                } catch(e) {
                    // Silently ignore override failures
                    console.debug('Languages override skipped:', e.message);
                }
            """)

            # Apply comprehensive stealth script
            self.driver.execute_script("""
                // Safe property override function
                function safeDefineProperty(obj, prop, descriptor) {
                    try {
                        const existing = Object.getOwnPropertyDescriptor(obj, prop);
                        if (!existing || existing.configurable) {
                            Object.defineProperty(obj, prop, descriptor);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        return false;
                    }
                }

                // Override webdriver property safely
                safeDefineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });

                // Override platform safely
                safeDefineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                    configurable: true
                });

                // Override permissions API
                if (navigator.permissions && navigator.permissions.query) {
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                }

                // Remove automation indicators
                if (window.chrome && window.chrome.runtime) {
                    safeDefineProperty(window.chrome.runtime, 'onConnect', {
                        value: undefined,
                        configurable: true
                    });
                }
            """)

        except Exception as e:
            print(f"Warning: Some stealth settings failed to apply: {e}")
    
    def start_driver(self,
                    headless: bool = False,
                    proxy: Optional[str] = None,
                    user_agent: Optional[str] = None,
                    window_size: tuple = (1920, 1080),
                    custom_options: List[str] = None,
                    use_undetected: bool = True) -> webdriver.Chrome:
        """Start Chrome driver with bot bypass configurations"""
        
        try:
            options = self._setup_chrome_options(
                headless=headless,
                proxy=proxy,
                user_agent=user_agent,
                window_size=window_size,
                custom_options=custom_options,
                use_undetected=use_undetected
            )
            
            print(f"🚀 Starting Chrome driver for profile: {self.profile_name}")
            print(f"   Use undetected: {use_undetected}")
            print(f"   Profile path: {self.profile_path}")
            print(f"   Headless: {headless}")

            if use_undetected:
                # Use undetected-chromedriver for better bot bypass
                try:
                    print(f"📦 Attempting undetected Chrome...")

                    # For imported profiles, undetected-chrome handles user-data-dir differently
                    # Remove user-data-dir from options and let undetected-chrome handle it
                    uc_options = self._setup_chrome_options(
                        headless=headless,
                        proxy=proxy,
                        user_agent=user_agent,
                        window_size=window_size,
                        custom_options=custom_options,
                        use_undetected=True,
                        skip_user_data_dir=True  # Skip user-data-dir for undetected
                    )

                    self.driver = uc.Chrome(
                        options=uc_options,
                        version_main=None,
                        user_data_dir=str(self.profile_path)  # Let undetected handle this
                    )
                    print(f"✅ Undetected Chrome started successfully")

                except Exception as e:
                    print(f"⚠️ Undetected Chrome failed: {e}")
                    print(f"🔄 Falling back to regular Chrome...")

                    # Fallback to regular webdriver
                    service = Service(WDM().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    print(f"✅ Regular Chrome started as fallback")
            else:
                # Use regular selenium webdriver with auto-managed ChromeDriver
                print(f"📦 Using regular Chrome driver...")
                service = Service(WDM().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ Regular Chrome started successfully")
            
            # Apply additional stealth settings
            self._apply_stealth_settings()

            # Initialize Gmail manager
            self.gmail_manager = GmailManager(self.driver)

            # Random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))

            return self.driver
            
        except Exception as e:
            print(f"Error starting Chrome driver: {e}")
            raise
    
    def navigate_to(self, url: str, wait_time: int = 5):
        """Navigate to URL with human-like behavior"""
        if not self.driver:
            raise Exception("Driver not started. Call start_driver() first.")
        
        try:
            self.driver.get(url)
            
            # Random wait to mimic human behavior
            time.sleep(random.uniform(2, wait_time))
            
            # Scroll randomly to mimic human behavior
            self._random_scroll()
            
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            raise
    
    def _random_scroll(self):
        """Perform random scrolling to mimic human behavior"""
        if not self.driver:
            return
        
        try:
            # Random scroll down
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Sometimes scroll back up
            if random.random() < 0.3:
                scroll_back = random.randint(50, scroll_amount)
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
                time.sleep(random.uniform(0.5, 1))
                
        except Exception as e:
            print(f"Error during random scroll: {e}")
    
    def human_type(self, element, text: str, typing_speed: float = 0.1):
        """Type text with human-like speed and behavior"""
        element.clear()
        
        for char in text:
            element.send_keys(char)
            # Random typing speed
            time.sleep(random.uniform(typing_speed * 0.5, typing_speed * 1.5))
            
            # Occasionally pause longer (like thinking)
            if random.random() < 0.1:
                time.sleep(random.uniform(0.5, 1.5))
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for element to be present and return it"""
        if not self.driver:
            raise Exception("Driver not started.")
        
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    def save_profile_data(self, data: Dict[str, Any]):
        """Save profile-specific data"""
        profile_data_file = self.profile_path / "profile_data.json"
        
        try:
            with open(profile_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profile data: {e}")
    
    def load_profile_data(self) -> Dict[str, Any]:
        """Load profile-specific data"""
        profile_data_file = self.profile_path / "profile_data.json"
        
        try:
            if profile_data_file.exists():
                with open(profile_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading profile data: {e}")
        
        return {}
    
    def auto_login_gmail(self, email, password, recovery_email=None, phone=None, tfa_secret=None):
        """Auto-login to Gmail account"""
        if not self.gmail_manager:
            print("❌ Gmail manager not initialized")
            return False

        return self.gmail_manager.auto_login(
            email=email,
            password=password,
            recovery_email=recovery_email,
            phone=phone,
            tfa_secret=tfa_secret
        )

    def get_gmail_account_info(self):
        """Get current Gmail account information"""
        if not self.gmail_manager:
            return None
        return self.gmail_manager.get_account_info()

    def logout_gmail(self):
        """Logout from Gmail"""
        if not self.gmail_manager:
            return False
        return self.gmail_manager.logout()

    def test_gmail_access(self):
        """Test if Gmail is accessible and logged in"""
        try:
            print(f"🧪 Testing Gmail access for profile: {self.profile_name}")

            # Navigate to Gmail
            self.driver.get("https://mail.google.com")
            time.sleep(5)

            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}")

            # Check if we're logged in
            if "mail.google.com" in current_url and "inbox" in current_url.lower():
                print(f"✅ Gmail access successful - already logged in")
                return True
            elif "accounts.google.com" in current_url:
                print(f"⚠️ Redirected to login page - not logged in")
                return False
            elif "workspace.google.com" in current_url:
                print(f"⚠️ Redirected to Google Workspace page - trying direct Gmail access")
                # Try direct Gmail inbox URL
                self.driver.get("https://mail.google.com/mail/u/0/#inbox")
                time.sleep(5)

                new_url = self.driver.current_url
                print(f"📍 After direct access: {new_url}")

                if "mail.google.com" in new_url and "inbox" in new_url.lower():
                    print(f"✅ Gmail access successful after direct navigation")
                    return True
                elif "accounts.google.com" in new_url:
                    print(f"⚠️ Still redirected to login - not logged in")
                    return False
                else:
                    print(f"❓ Still unknown state after direct access: {new_url}")
                    return False
            else:
                print(f"❓ Unknown state - URL: {current_url}")
                return False

        except Exception as e:
            print(f"❌ Error testing Gmail access: {e}")
            return False

    def force_gmail_login_check(self):
        """Force check Gmail login status with multiple attempts"""
        try:
            print(f"🔍 Force checking Gmail login status...")

            # Try multiple Gmail URLs
            gmail_urls = [
                "https://mail.google.com/mail/u/0/#inbox",
                "https://gmail.com",
                "https://accounts.google.com/signin/v2/identifier?service=mail"
            ]

            for i, url in enumerate(gmail_urls):
                print(f"🌐 Attempt {i+1}: Trying {url}")
                self.driver.get(url)
                time.sleep(5)

                current_url = self.driver.current_url
                print(f"📍 Result URL: {current_url}")

                # Check for successful Gmail access
                if "mail.google.com" in current_url and ("inbox" in current_url or "mail" in current_url):
                    print(f"✅ Gmail accessible via {url}")
                    return True

                # Check if we need to login
                if "accounts.google.com" in current_url:
                    print(f"🔐 Login required - stopped at login page")
                    return False

            print(f"❌ Could not access Gmail with any URL")
            return False

        except Exception as e:
            print(f"❌ Error in force Gmail check: {e}")
            return False

    def execute_script(self, script_name: str, **kwargs):
        """Execute a Selenium script on this driver"""
        if not self.driver:
            return {
                "success": False,
                "message": "Browser not running",
                "error": "Driver not initialized"
            }

        print(f"🚀 Executing script: {script_name} on profile: {self.profile_name}")

        result = self.script_manager.execute_script(
            script_name=script_name,
            driver=self.driver,
            profile_name=self.profile_name,
            **kwargs
        )

        print(f"📊 Script result: {result.message}")
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp
        }

    def list_available_scripts(self):
        """List all available scripts"""
        scripts = self.script_manager.list_scripts()
        return [
            {
                "name": script.name,
                "display_name": script.display_name,
                "description": script.description,
                "file_path": script.file_path,
                "created_at": script.created_at
            }
            for script in scripts
        ]

    def run_ai_generation_batch(self, prompt_file: str, platform: str, **kwargs):
        """Run batch AI image generation from prompt file"""
        if not self.driver:
            return {
                "success": False,
                "message": "Browser not running",
                "error": "Driver not initialized"
            }

        try:
            print(f"🚀 Starting AI image generation batch")
            print(f"   Platform: {platform}")
            print(f"   Prompt file: {prompt_file}")
            print(f"   Profile: {self.profile_name}")

            # Load prompts
            prompts = self.prompt_manager.load_prompts_from_file(prompt_file)
            pending_prompts = self.prompt_manager.get_pending_prompts(prompts)

            print(f"📋 Loaded {len(prompts)} prompts, {len(pending_prompts)} pending")

            if not pending_prompts:
                return {
                    "success": True,
                    "message": "No pending prompts to process",
                    "data": {"total_prompts": len(prompts), "pending_prompts": 0}
                }

            # Create AI generator
            generator = create_generator(self.driver, platform, **kwargs)

            # Process prompts
            results = []
            successful = 0
            failed = 0

            for i, prompt in enumerate(pending_prompts, 1):
                print(f"\n🎨 Processing prompt {i}/{len(pending_prompts)}: {prompt.text[:50]}...")

                # Update status
                self.prompt_manager.update_prompt_status(prompt, "processing")

                # Generate image
                result = generator.generate_image(prompt)

                # Save result
                metadata_path = self.prompt_manager.save_result(result)

                # Update prompt status
                if result.success:
                    self.prompt_manager.update_prompt_status(prompt, "completed")
                    prompt.result_path = metadata_path
                    successful += 1
                    print(f"✅ Success: {len(result.image_paths)} images generated")
                else:
                    self.prompt_manager.update_prompt_status(prompt, "failed", result.error)
                    failed += 1
                    print(f"❌ Failed: {result.error}")

                results.append({
                    "prompt_id": prompt.id,
                    "prompt_text": prompt.text,
                    "success": result.success,
                    "image_count": len(result.image_paths) if result.image_paths else 0,
                    "generation_time": result.generation_time,
                    "error": result.error
                })

                # Add delay between generations
                if i < len(pending_prompts):
                    delay = kwargs.get('delay', 5)
                    print(f"⏳ Waiting {delay}s before next generation...")
                    time.sleep(delay)

            return {
                "success": True,
                "message": f"Batch completed: {successful} successful, {failed} failed",
                "data": {
                    "total_processed": len(pending_prompts),
                    "successful": successful,
                    "failed": failed,
                    "platform": platform,
                    "results": results
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Batch generation failed: {str(e)}",
                "error": str(e)
            }

    def list_prompt_files(self):
        """List available prompt files"""
        return self.prompt_manager.list_prompt_files()

    def get_generation_stats(self):
        """Get generation statistics"""
        try:
            # Count files in results directory
            results_dir = Path("results")
            images_dir = results_dir / "images"
            metadata_dir = results_dir / "metadata"
            logs_dir = Path("logs")

            stats = {
                "total_images": len(list(images_dir.glob("*"))) if images_dir.exists() else 0,
                "total_metadata": len(list(metadata_dir.glob("*"))) if metadata_dir.exists() else 0,
                "total_logs": len(list(logs_dir.glob("*"))) if logs_dir.exists() else 0,
                "results_dir_size": self._get_directory_size(results_dir) if results_dir.exists() else 0
            }

            return stats

        except Exception as e:
            return {"error": str(e)}

    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size

    def quit_driver(self):
        """Safely quit the driver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error quitting driver: {e}")
            finally:
                self.driver = None
                self.gmail_manager = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit_driver()
