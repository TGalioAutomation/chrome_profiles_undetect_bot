#!/usr/bin/env python3
"""
Gmail Manager for Chrome Profiles
Handles Gmail auto-login and account management
"""

import time
import random
import pyotp
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class GmailManager:
    """Manager for Gmail account operations"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def auto_login(self, email, password, recovery_email=None, phone=None, tfa_secret=None):
        """
        Automatically login to Gmail account

        Args:
            email: Gmail email address
            password: Gmail password
            recovery_email: Recovery email for verification
            phone: Phone number for verification
            tfa_secret: 2FA secret key for TOTP generation

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            print(f"🔐 Starting Gmail auto-login for {email}")

            # Apply additional stealth before login
            self._apply_gmail_stealth()

            # Navigate to Gmail with more natural approach
            self.driver.get("https://www.google.com")
            time.sleep(2)

            # Navigate to Gmail naturally
            self.driver.get("https://mail.google.com")
            time.sleep(3)

            # If redirected to login, proceed
            if "accounts.google.com" in self.driver.current_url or "signin" in self.driver.current_url.lower():
                print("🔄 Redirected to login page")
            else:
                # Try clicking Gmail sign in
                try:
                    sign_in_btn = self.driver.find_element(By.LINK_TEXT, "Sign in")
                    sign_in_btn.click()
                    time.sleep(2)
                except:
                    self.driver.get("https://accounts.google.com/signin/v2/identifier?service=mail")
                    time.sleep(3)
            
            # Step 1: Enter email
            if not self._enter_email(email):
                return False
            
            # Step 2: Enter password
            if not self._enter_password(password):
                return False

            # Step 2.5: Handle "browser not secure" error
            if not self._handle_browser_security_warning():
                return False
            
            # Step 3: Handle 2FA if needed
            if tfa_secret:
                if not self._handle_2fa(tfa_secret):
                    return False
            
            # Step 4: Handle other verifications
            if not self._handle_verification(recovery_email, phone):
                return False
            
            # Step 5: Navigate to Gmail
            self.driver.get("https://mail.google.com")
            time.sleep(3)
            
            # Verify login success
            if self._verify_gmail_login():
                print(f"✅ Gmail auto-login successful for {email}")
                return True
            else:
                print(f"❌ Gmail auto-login failed for {email}")
                return False
                
        except Exception as e:
            print(f"❌ Gmail auto-login error: {e}")
            return False

    def _apply_gmail_stealth(self):
        """Apply Gmail-specific stealth techniques"""
        try:
            # Remove automation indicators
            self.driver.execute_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });

                // Override automation detection
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', description: '', filename: 'internal-nacl-plugin'}
                    ],
                    configurable: true
                });

                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    configurable: true
                });

                // Override platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                    configurable: true
                });

                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Override chrome runtime
                if (window.chrome && window.chrome.runtime) {
                    Object.defineProperty(window.chrome.runtime, 'onConnect', {
                        value: undefined,
                        configurable: true
                    });
                }

                // Add realistic screen properties
                Object.defineProperty(screen, 'availTop', {
                    get: () => 0,
                    configurable: true
                });

                Object.defineProperty(screen, 'availLeft', {
                    get: () => 0,
                    configurable: true
                });
            """)

            print("✅ Gmail stealth techniques applied")

        except Exception as e:
            print(f"⚠️ Warning: Gmail stealth application failed: {e}")
    
    def _enter_email(self, email):
        """Enter email address with human-like behavior"""
        try:
            # Wait for email input with multiple selectors
            email_input = None
            selectors = [
                (By.ID, "identifierId"),
                (By.NAME, "identifier"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[autocomplete='username']")
            ]

            for selector in selectors:
                try:
                    email_input = self.wait.until(EC.presence_of_element_located(selector))
                    break
                except TimeoutException:
                    continue

            if not email_input:
                print("❌ Could not find email input field")
                return False

            # Clear and enter email with human-like typing
            email_input.clear()
            time.sleep(0.5)

            # Type email character by character with random delays
            for char in email:
                email_input.send_keys(char)
                time.sleep(0.05 + (0.1 * random.random()))

            time.sleep(1)

            # Find and click next button
            next_selectors = [
                (By.ID, "identifierNext"),
                (By.CSS_SELECTOR, "[data-primary='true']"),
                (By.CSS_SELECTOR, "button[type='button']"),
                (By.XPATH, "//span[text()='Next']/..")
            ]

            next_button = None
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(*selector)
                    break
                except NoSuchElementException:
                    continue

            if next_button:
                # Scroll to button if needed
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                next_button.click()
            else:
                # Try pressing Enter
                email_input.send_keys("\n")

            time.sleep(3)
            return True

        except Exception as e:
            print(f"❌ Failed to enter email: {e}")
            return False
    
    def _enter_password(self, password):
        """Enter password with human-like behavior"""
        try:
            # Wait for password input with multiple selectors
            password_input = None
            selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
                (By.ID, "password")
            ]

            for selector in selectors:
                try:
                    password_input = self.wait.until(EC.element_to_be_clickable(selector))
                    break
                except TimeoutException:
                    continue

            if not password_input:
                print("❌ Could not find password input field")
                return False

            # Clear and enter password with human-like typing
            password_input.clear()
            time.sleep(0.5)

            # Type password character by character with random delays
            for char in password:
                password_input.send_keys(char)
                time.sleep(0.05 + (0.1 * random.random()))

            time.sleep(1)

            # Find and click next button
            next_selectors = [
                (By.ID, "passwordNext"),
                (By.CSS_SELECTOR, "[data-primary='true']"),
                (By.CSS_SELECTOR, "button[type='button']"),
                (By.XPATH, "//span[text()='Next']/..")
            ]

            next_button = None
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(*selector)
                    break
                except NoSuchElementException:
                    continue

            if next_button:
                # Scroll to button if needed
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                next_button.click()
            else:
                # Try pressing Enter
                password_input.send_keys("\n")

            time.sleep(4)
            return True

        except Exception as e:
            print(f"❌ Failed to enter password: {e}")
            return False

    def _handle_browser_security_warning(self):
        """Handle 'This browser or app may not be secure' warning"""
        try:
            time.sleep(2)

            # Check for security warning
            warning_texts = [
                "This browser or app may not be secure",
                "browser or app may not be secure",
                "Try using a different browser",
                "Couldn't sign you in"
            ]

            page_text = self.driver.page_source.lower()
            has_warning = any(text.lower() in page_text for text in warning_texts)

            if has_warning:
                print("⚠️ Detected browser security warning, attempting bypass...")

                # Try clicking "Try again" or "Continue" buttons
                continue_selectors = [
                    (By.XPATH, "//span[contains(text(), 'Try again')]/../.."),
                    (By.XPATH, "//span[contains(text(), 'Continue')]/../.."),
                    (By.XPATH, "//button[contains(text(), 'Try again')]"),
                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                    (By.CSS_SELECTOR, "[data-action='tryAgain']"),
                    (By.CSS_SELECTOR, "[data-action='continue']")
                ]

                for selector in continue_selectors:
                    try:
                        button = self.driver.find_element(*selector)
                        if button.is_displayed():
                            button.click()
                            time.sleep(3)
                            print("✅ Clicked continue button")
                            break
                    except NoSuchElementException:
                        continue

                # Alternative: Try going directly to Gmail
                try:
                    self.driver.get("https://mail.google.com/mail/u/0/#inbox")
                    time.sleep(3)

                    # Check if we're logged in
                    if "mail.google.com" in self.driver.current_url and "inbox" in self.driver.current_url:
                        print("✅ Successfully bypassed security warning")
                        return True
                except:
                    pass

                # If still on warning page, try alternative login method
                if any(text.lower() in self.driver.page_source.lower() for text in warning_texts):
                    print("⚠️ Still on security warning page, trying alternative method...")
                    return self._try_alternative_login()

            return True

        except Exception as e:
            print(f"⚠️ Warning: Browser security check failed: {e}")
            return True  # Continue anyway

    def _try_alternative_login(self):
        """Try alternative login method when security warning appears"""
        try:
            # Method 1: Try using different Gmail URL
            alternative_urls = [
                "https://accounts.google.com/signin/v2/identifier?service=mail&continue=https://mail.google.com/mail/&flowName=GlifWebSignIn&flowEntry=ServiceLogin",
                "https://accounts.google.com/AccountChooser?service=mail&continue=https://mail.google.com/mail/",
                "https://mail.google.com/mail/u/0/"
            ]

            for url in alternative_urls:
                try:
                    self.driver.get(url)
                    time.sleep(3)

                    # Check if we're past the security warning
                    if "mail.google.com" in self.driver.current_url:
                        print(f"✅ Alternative URL worked: {url}")
                        return True

                except Exception as e:
                    print(f"Alternative URL failed: {e}")
                    continue

            # Method 2: Try clearing cookies and starting fresh
            print("🔄 Trying fresh session...")
            self.driver.delete_all_cookies()
            time.sleep(1)

            # Navigate to Google first, then Gmail
            self.driver.get("https://www.google.com")
            time.sleep(2)
            self.driver.get("https://mail.google.com")
            time.sleep(3)

            return True

        except Exception as e:
            print(f"❌ Alternative login method failed: {e}")
            return False
    
    def _handle_2fa(self, tfa_secret):
        """Handle 2FA verification"""
        try:
            # Check if 2FA is required
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.ID, "totpPin"))
                )
            except TimeoutException:
                # 2FA not required
                return True
            
            # Generate TOTP code
            totp = pyotp.TOTP(tfa_secret)
            code = totp.now()
            
            # Enter 2FA code
            tfa_input = self.driver.find_element(By.ID, "totpPin")
            tfa_input.clear()
            tfa_input.send_keys(code)
            
            next_button = self.driver.find_element(By.ID, "totpNext")
            next_button.click()
            
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Failed to handle 2FA: {e}")
            return False
    
    def _handle_verification(self, recovery_email=None, phone=None):
        """Handle additional verification steps"""
        try:
            # Check for verification challenges
            time.sleep(2)
            
            # Handle recovery email verification
            if recovery_email:
                try:
                    recovery_input = self.driver.find_element(By.ID, "knowledge-preregistered-email-response")
                    recovery_input.clear()
                    recovery_input.send_keys(recovery_email)
                    
                    next_button = self.driver.find_element(By.ID, "next")
                    next_button.click()
                    time.sleep(2)
                except NoSuchElementException:
                    pass
            
            # Handle phone verification
            if phone:
                try:
                    phone_input = self.driver.find_element(By.ID, "knowledge-preregistered-phone-response")
                    phone_input.clear()
                    phone_input.send_keys(phone)
                    
                    next_button = self.driver.find_element(By.ID, "next")
                    next_button.click()
                    time.sleep(2)
                except NoSuchElementException:
                    pass
            
            return True
            
        except Exception as e:
            print(f"⚠️ Verification handling warning: {e}")
            return True  # Continue even if verification fails
    
    def _verify_gmail_login(self):
        """Verify that Gmail login was successful"""
        try:
            # Check for Gmail interface elements
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-tooltip='Gmail']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Gmail']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".nH")),  # Gmail main container
                    EC.url_contains("mail.google.com")
                )
            )
            return True
            
        except TimeoutException:
            return False
    
    def get_account_info(self):
        """Get current Gmail account information"""
        try:
            # Try to get account info from Gmail interface
            account_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-tooltip*='@']")
            if account_elements:
                return account_elements[0].get_attribute("data-tooltip")
            
            # Alternative method
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label*='Google Account']")
            if profile_elements:
                return profile_elements[0].get_attribute("aria-label")
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get account info: {e}")
            return None
    
    def logout(self):
        """Logout from Gmail"""
        try:
            # Navigate to logout URL
            self.driver.get("https://accounts.google.com/logout")
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Failed to logout: {e}")
            return False
