#!/usr/bin/env python3
"""
AI Image Generation Automation
Handles automation of AI image generation platforms
"""

import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.core import driver

from .prompt_manager import Prompt, GenerationResult
from datetime import datetime

class AIImageGenerator:
    """Base class for AI image generation automation"""
    
    def __init__(self, driver, platform: str = "generic"):
        self.driver = driver
        self.platform = platform
        self.wait = WebDriverWait(driver, 30)
        self.results_dir = Path("results/images")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_image(self, prompt: Prompt) -> GenerationResult:
        """Generate image from prompt - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_image method")
    
    def download_image(self, image_url: str, filename: str) -> str:
        """Download image from URL"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            file_path = self.results_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return None


class LeonardoGenerator(AIImageGenerator):
    """Leonardo automation via Discord"""

    button_dimensions_xpath = "//button[.//p[text()='16:9']]"
    textarea_xpath = "//textarea[@id='prompt-textarea']"
    button_generate_xpath = "//button[.//span[text()='Generate']]"
    def __init__(self, driver):
        driver = driver.driver if hasattr(driver, 'driver') else driver
        super().__init__(driver, "Leonardo")
        self.leonardo_url = "https://app.leonardo.ai/image-generation"

    def generate_image(self, prompt: Prompt) -> GenerationResult:
        """Generate image using Leonardo"""
        start_time = time.time()

        try:
            print(f"🎨 Generating Leonardo image for: {prompt.text[:50]}...")

            # Navigate to Leonardo Discord
            self.driver.get(self.leonardo_url)
            time.sleep(5)

            try:
                print("⏳ Waiting for '16:9' aspect ratio button...")
                dimension_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.button_dimensions_xpath))
                )
                dimension_button.click()
                print("✅ Selected '16:9' aspect ratio.")
            except TimeoutException:
                print("⚠️ Could not find or click '16:9' button, proceeding with default aspect ratio.")

            try:
                textarea = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.textarea_xpath))
                )
                textarea.clear()
                textarea.send_keys(prompt.text)
            except NoSuchElementException:
                print("❌ Could not find textarea element.")
            # Press Enter to send
            # try:
            #     button_generate = self.wait.until(
            #         EC.element_to_be_clickable((By.XPATH, self.button_generate_xpath))
            #     )
            #     button_generate.click()
            # except NoSuchElementException:
            #     print("❌ Could not find button_generate element.")

            # Wait for generation to complete (this is simplified)
            print("⏳ Waiting for image generation...")
            time.sleep(60)  # Leonardo typically takes 30-60 seconds

            # Look for generated images (simplified - would need more complex logic)
            images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='cdn.discordapp.com']")

            image_paths = []
            if images:
                for i, img in enumerate(images[-4:]):  # Get last 4 images (Leonardo grid)
                    img_url = img.get_attribute('src')
                    if img_url and 'cdn.discordapp.com' in img_url:
                        filename = f"Leonardo_{prompt.id}_{i + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        downloaded_path = self.download_image(img_url, filename)
                        if downloaded_path:
                            image_paths.append(downloaded_path)

            execution_time = time.time() - start_time

            if image_paths:
                return GenerationResult(
                    prompt_id=prompt.id,
                    success=True,
                    image_paths=image_paths,
                    generation_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "platform": "Leonardo",
                        "prompt": prompt.text,
                        "image_count": len(image_paths)
                    }
                )
            else:
                return GenerationResult(
                    prompt_id=prompt.id,
                    success=False,
                    generation_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    error="No images found after generation"
                )

        except Exception as e:
            return GenerationResult(
                prompt_id=prompt.id,
                success=False,
                generation_time=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

class MidjourneyGenerator(AIImageGenerator):
    """Midjourney automation via Discord"""
    
    def __init__(self, driver):
        super().__init__(driver, "midjourney")
        self.discord_url = "https://discord.com/channels/662267976984297473/1008571070446637116"
    
    def generate_image(self, prompt: Prompt) -> GenerationResult:
        """Generate image using Midjourney"""
        start_time = time.time()
        
        try:
            print(f"🎨 Generating Midjourney image for: {prompt.text[:50]}...")
            
            # Navigate to Midjourney Discord
            self.driver.get(self.discord_url)
            time.sleep(5)
            
            # Find message input
            message_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-slate-editor='true']"))
            )
            
            # Type /imagine command
            imagine_command = f"/imagine {prompt.text}"
            message_input.click()
            message_input.clear()
            message_input.send_keys(imagine_command)
            time.sleep(2)
            
            # Press Enter to send
            message_input.send_keys("\n")
            
            # Wait for generation to complete (this is simplified)
            print("⏳ Waiting for image generation...")
            time.sleep(60)  # Midjourney typically takes 30-60 seconds
            
            # Look for generated images (simplified - would need more complex logic)
            images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='cdn.discordapp.com']")
            
            image_paths = []
            if images:
                for i, img in enumerate(images[-4:]):  # Get last 4 images (Midjourney grid)
                    img_url = img.get_attribute('src')
                    if img_url and 'cdn.discordapp.com' in img_url:
                        filename = f"midjourney_{prompt.id}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        downloaded_path = self.download_image(img_url, filename)
                        if downloaded_path:
                            image_paths.append(downloaded_path)
            
            execution_time = time.time() - start_time
            
            if image_paths:
                return GenerationResult(
                    prompt_id=prompt.id,
                    success=True,
                    image_paths=image_paths,
                    generation_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "platform": "midjourney",
                        "prompt": prompt.text,
                        "image_count": len(image_paths)
                    }
                )
            else:
                return GenerationResult(
                    prompt_id=prompt.id,
                    success=False,
                    generation_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    error="No images found after generation"
                )
                
        except Exception as e:
            return GenerationResult(
                prompt_id=prompt.id,
                success=False,
                generation_time=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

class StableDiffusionGenerator(AIImageGenerator):
    """Stable Diffusion automation (web interface)"""
    
    def __init__(self, driver, base_url: str = "http://localhost:7860"):
        super().__init__(driver, "stable_diffusion")
        self.base_url = base_url
    
    def generate_image(self, prompt: Prompt) -> GenerationResult:
        """Generate image using Stable Diffusion web UI"""
        start_time = time.time()
        
        try:
            print(f"🎨 Generating Stable Diffusion image for: {prompt.text[:50]}...")
            
            # Navigate to Stable Diffusion web UI
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Find prompt input
            prompt_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#txt2img_prompt textarea"))
            )
            
            # Enter prompt
            prompt_input.clear()
            prompt_input.send_keys(prompt.text)
            
            # Set parameters if provided
            if prompt.parameters:
                self._set_parameters(prompt.parameters)
            
            # Click generate button
            generate_btn = self.driver.find_element(By.CSS_SELECTOR, "#txt2img_generate")
            generate_btn.click()
            
            # Wait for generation to complete
            print("⏳ Waiting for image generation...")
            self._wait_for_generation_complete()
            
            # Get generated image
            image_paths = self._download_generated_images(prompt.id)
            
            execution_time = time.time() - start_time
            
            if image_paths:
                return GenerationResult(
                    prompt_id=prompt.id,
                    success=True,
                    image_paths=image_paths,
                    generation_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "platform": "stable_diffusion",
                        "prompt": prompt.text,
                        "parameters": prompt.parameters
                    }
                )
            else:
                return GenerationResult(
                    prompt_id=prompt.id,
                    success=False,
                    generation_time=execution_time,
                    timestamp=datetime.now().isoformat(),
                    error="No images generated"
                )
                
        except Exception as e:
            return GenerationResult(
                prompt_id=prompt.id,
                success=False,
                generation_time=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    def _set_parameters(self, parameters: Dict[str, Any]):
        """Set generation parameters"""
        try:
            # Set steps
            if 'steps' in parameters:
                steps_input = self.driver.find_element(By.CSS_SELECTOR, "#txt2img_steps input")
                steps_input.clear()
                steps_input.send_keys(str(parameters['steps']))
            
            # Set CFG scale
            if 'cfg_scale' in parameters:
                cfg_input = self.driver.find_element(By.CSS_SELECTOR, "#txt2img_cfg_scale input")
                cfg_input.clear()
                cfg_input.send_keys(str(parameters['cfg_scale']))
            
            # Set width/height
            if 'width' in parameters:
                width_input = self.driver.find_element(By.CSS_SELECTOR, "#txt2img_width input")
                width_input.clear()
                width_input.send_keys(str(parameters['width']))
            
            if 'height' in parameters:
                height_input = self.driver.find_element(By.CSS_SELECTOR, "#txt2img_height input")
                height_input.clear()
                height_input.send_keys(str(parameters['height']))
                
        except Exception as e:
            print(f"⚠️ Warning: Could not set some parameters: {e}")
    
    def _wait_for_generation_complete(self):
        """Wait for generation to complete"""
        try:
            # Wait for progress bar to appear and disappear
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".progress"))
            )
            
            # Wait for progress to complete (progress bar disappears)
            WebDriverWait(self.driver, 120).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".progress"))
            )
            
        except TimeoutException:
            print("⚠️ Generation timeout or no progress indicator found")
    
    def _download_generated_images(self, prompt_id: str) -> List[str]:
        """Download generated images"""
        image_paths = []
        
        try:
            # Find generated images
            images = self.driver.find_elements(By.CSS_SELECTOR, "#txt2img_gallery img")
            
            for i, img in enumerate(images):
                img_src = img.get_attribute('src')
                if img_src and img_src.startswith('data:image'):
                    # Handle base64 images
                    filename = f"sd_{prompt_id}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    file_path = self._save_base64_image(img_src, filename)
                    if file_path:
                        image_paths.append(file_path)
                elif img_src:
                    # Handle URL images
                    filename = f"sd_{prompt_id}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    downloaded_path = self.download_image(img_src, filename)
                    if downloaded_path:
                        image_paths.append(downloaded_path)
                        
        except Exception as e:
            print(f"❌ Error downloading images: {e}")
        
        return image_paths
    
    def _save_base64_image(self, base64_data: str, filename: str) -> str:
        """Save base64 image data"""
        try:
            import base64
            
            # Extract base64 data
            header, data = base64_data.split(',', 1)
            image_data = base64.b64decode(data)
            
            file_path = self.results_dir / filename
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error saving base64 image: {e}")
            return None

def create_generator(driver, platform: str, **kwargs) -> AIImageGenerator:
    """Factory function to create appropriate generator"""
    
    if platform.lower() == "midjourney":
        return MidjourneyGenerator(driver)
    elif platform.lower() == "leonardo":
        return LeonardoGenerator(driver)
    elif platform.lower() == "stable_diffusion":
        base_url = kwargs.get('base_url', 'http://localhost:7860')
        return StableDiffusionGenerator(driver, base_url)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
