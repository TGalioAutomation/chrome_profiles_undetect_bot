#!/usr/bin/env python3
"""
Thread Manager for Multi-Threading AI Image Generation
Handles concurrent processing of multiple prompts
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import traceback

from .prompt_manager import Prompt, GenerationResult, PromptManager
from .ai_image_generator import create_generator

@dataclass
class ThreadConfig:
    """Configuration for thread pool"""
    max_workers: int = 3
    timeout: int = 300  # 5 minutes per generation
    retry_attempts: int = 2
    delay_between_batches: float = 1.0
    delay_between_retries: float = 5.0

@dataclass
class GenerationTask:
    """Single generation task"""
    prompt: Prompt
    platform: str
    parameters: Dict[str, Any]
    attempt: int = 1
    max_attempts: int = 2

@dataclass
class BatchProgress:
    """Progress tracking for batch generation"""
    total_prompts: int = 0
    completed: int = 0
    successful: int = 0
    failed: int = 0
    in_progress: int = 0
    start_time: float = 0
    results: List[GenerationResult] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    @property
    def progress_percentage(self) -> float:
        if self.total_prompts == 0:
            return 0
        return (self.completed / self.total_prompts) * 100
    
    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time
    
    @property
    def estimated_remaining(self) -> float:
        if self.completed == 0:
            return 0
        avg_time_per_prompt = self.elapsed_time / self.completed
        remaining_prompts = self.total_prompts - self.completed
        return avg_time_per_prompt * remaining_prompts

class MultiThreadGenerator:
    """Multi-threaded AI image generator"""
    
    def __init__(self, profile_manager, config: ThreadConfig = None):
        self.profile_manager = profile_manager
        self.config = config or ThreadConfig()
        self.prompt_manager = PromptManager()
        
        # Thread management
        self.executor = None
        self.active_tasks = {}
        self.progress = BatchProgress()
        self.is_running = False
        self.stop_requested = False
        
        # Thread-safe progress tracking
        self.progress_lock = threading.Lock()
        self.results_queue = Queue()
        
        # Callbacks
        self.progress_callback = None
        self.completion_callback = None
    
    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[BatchProgress], None]):
        """Set callback for batch completion"""
        self.completion_callback = callback
    
    def start_batch_generation(self, 
                             prompts: List[Prompt], 
                             platform: str, 
                             drivers: List[Any],
                             **kwargs) -> str:
        """Start multi-threaded batch generation"""
        
        if self.is_running:
            raise RuntimeError("Batch generation already in progress")
        
        # Initialize progress tracking
        with self.progress_lock:
            self.progress = BatchProgress(
                total_prompts=len(prompts),
                start_time=time.time()
            )
            self.is_running = True
            self.stop_requested = False
        
        # Create tasks
        tasks = [
            GenerationTask(
                prompt=prompt,
                platform=platform,
                parameters=kwargs,
                max_attempts=self.config.retry_attempts
            )
            for prompt in prompts
        ]
        
        # Start thread pool
        self.executor = ThreadPoolExecutor(
            max_workers=min(self.config.max_workers, len(drivers))
        )
        
        # Submit tasks
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background thread to manage generation
        generation_thread = threading.Thread(
            target=self._run_batch_generation,
            args=(tasks, drivers, batch_id),
            daemon=True
        )
        generation_thread.start()
        
        return batch_id
    
    def _run_batch_generation(self, tasks: List[GenerationTask], drivers: List[Any], batch_id: str):
        """Run batch generation in background thread"""
        try:
            print(f"🚀 Starting multi-threaded batch generation: {batch_id}")
            print(f"📊 Tasks: {len(tasks)}, Workers: {self.config.max_workers}, Drivers: {len(drivers)}")
            
            # Create driver pool
            driver_queue = Queue()
            for driver in drivers:
                driver_queue.put(driver)
            
            # Submit all tasks
            future_to_task = {}
            
            for task in tasks:
                if self.stop_requested:
                    break
                
                future = self.executor.submit(
                    self._process_single_task,
                    task, driver_queue, batch_id
                )
                future_to_task[future] = task
                
                # Update in_progress count
                with self.progress_lock:
                    self.progress.in_progress += 1
                
                # Small delay between submissions
                time.sleep(self.config.delay_between_batches)
            
            # Process completed tasks
            for future in as_completed(future_to_task, timeout=self.config.timeout * len(tasks)):
                if self.stop_requested:
                    break
                
                task = future_to_task[future]
                
                try:
                    result = future.result()
                    self._handle_task_completion(task, result)
                    
                except Exception as e:
                    print(f"❌ Task failed: {task.prompt.id} - {str(e)}")
                    error_result = GenerationResult(
                        prompt_id=task.prompt.id,
                        success=False,
                        timestamp=datetime.now().isoformat(),
                        error=str(e)
                    )
                    self._handle_task_completion(task, error_result)
            
            # Finalize batch
            self._finalize_batch(batch_id)
            
        except Exception as e:
            print(f"❌ Batch generation error: {e}")
            traceback.print_exc()
        finally:
            self._cleanup()
    
    def _process_single_task(self, task: GenerationTask, driver_queue: Queue, batch_id: str) -> GenerationResult:
        """Process a single generation task"""
        driver = None
        
        try:
            # Get available driver
            driver = driver_queue.get(timeout=30)
            
            print(f"🎨 Processing: {task.prompt.text[:50]}... (Attempt {task.attempt})")
            
            # Create generator for this driver
            generator = create_generator(driver, task.platform, **task.parameters)
            
            # Update prompt status
            self.prompt_manager.update_prompt_status(task.prompt, "processing")
            
            # Generate image
            result = generator.generate_image(task.prompt)
            
            # Save result
            if result.success:
                metadata_path = self.prompt_manager.save_result(result)
                self.prompt_manager.update_prompt_status(task.prompt, "completed")
                task.prompt.result_path = metadata_path
                print(f"✅ Success: {task.prompt.id} - {len(result.image_paths or [])} images")
            else:
                self.prompt_manager.update_prompt_status(task.prompt, "failed", result.error)
                print(f"❌ Failed: {task.prompt.id} - {result.error}")
            
            return result
            
        except Exception as e:
            error_msg = f"Task processing error: {str(e)}"
            print(f"❌ {error_msg}")
            
            return GenerationResult(
                prompt_id=task.prompt.id,
                success=False,
                timestamp=datetime.now().isoformat(),
                error=error_msg
            )
            
        finally:
            # Return driver to pool
            if driver:
                driver_queue.put(driver)
    
    def _handle_task_completion(self, task: GenerationTask, result: GenerationResult):
        """Handle completion of a single task"""
        with self.progress_lock:
            self.progress.completed += 1
            self.progress.in_progress -= 1
            self.progress.results.append(result)
            
            if result.success:
                self.progress.successful += 1
            else:
                self.progress.failed += 1
            
            # Call progress callback
            if self.progress_callback:
                try:
                    self.progress_callback(self.progress)
                except Exception as e:
                    print(f"⚠️ Progress callback error: {e}")
    
    def _finalize_batch(self, batch_id: str):
        """Finalize batch generation"""
        with self.progress_lock:
            print(f"🎉 Batch completed: {batch_id}")
            print(f"📊 Results: {self.progress.successful} successful, {self.progress.failed} failed")
            print(f"⏱️ Total time: {self.progress.elapsed_time:.1f}s")
            
            # Call completion callback
            if self.completion_callback:
                try:
                    self.completion_callback(self.progress)
                except Exception as e:
                    print(f"⚠️ Completion callback error: {e}")
    
    def _cleanup(self):
        """Cleanup resources"""
        with self.progress_lock:
            self.is_running = False
        
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
    
    def stop_generation(self):
        """Stop ongoing generation"""
        print("🛑 Stopping batch generation...")
        self.stop_requested = True
        
        if self.executor:
            self.executor.shutdown(wait=False)
        
        self._cleanup()
    
    def get_progress(self) -> BatchProgress:
        """Get current progress"""
        with self.progress_lock:
            return self.progress
    
    def is_generation_running(self) -> bool:
        """Check if generation is running"""
        return self.is_running

class ProfileDriverPool:
    """Pool of Chrome drivers from multiple profiles"""
    
    def __init__(self, profile_manager):
        self.profile_manager = profile_manager
        self.active_drivers = {}
    
    def get_available_drivers(self) -> List[Any]:
        """Get list of available Chrome drivers"""
        return list(self.active_drivers.values())
    
    def add_driver(self, profile_name: str, driver_manager):
        """Add driver to pool"""
        self.active_drivers[profile_name] = driver_manager
    
    def remove_driver(self, profile_name: str):
        """Remove driver from pool"""
        if profile_name in self.active_drivers:
            del self.active_drivers[profile_name]
    
    def get_driver_count(self) -> int:
        """Get number of available drivers"""
        return len(self.active_drivers)
