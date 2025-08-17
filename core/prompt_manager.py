#!/usr/bin/env python3
"""
Prompt Manager for AI Image Generation
Handles reading, parsing, and managing prompts for automation
"""

import os
import json
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Directories
PROMPTS_DIR = Path("prompts")
RESULTS_DIR = Path("results")
LOGS_DIR = Path("logs")

# Create directories
for dir_path in [PROMPTS_DIR, RESULTS_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

@dataclass
class Prompt:
    """Single prompt data structure"""
    id: str
    text: str
    parameters: Dict[str, Any] = None
    category: str = "default"
    priority: int = 1
    status: str = "pending"  # pending, processing, completed, failed
    created_at: str = None
    processed_at: str = None
    result_path: str = None
    error: str = None

@dataclass
class GenerationResult:
    """Result of image generation"""
    prompt_id: str
    success: bool
    image_paths: List[str] = None
    generation_time: float = 0
    timestamp: str = None
    metadata: Dict[str, Any] = None
    error: str = None

class PromptManager:
    """Manager for AI image generation prompts"""
    
    def __init__(self):
        self.prompts_dir = PROMPTS_DIR
        self.results_dir = RESULTS_DIR
        self.logs_dir = LOGS_DIR
        
        # Create subdirectories
        (self.results_dir / "images").mkdir(exist_ok=True)
        (self.results_dir / "metadata").mkdir(exist_ok=True)
        
        # Create example prompt files
        self._create_example_files()
    
    def _create_example_files(self):
        """Create example prompt files"""
        
        # Example TXT file
        txt_example = self.prompts_dir / "example_prompts.txt"
        if not txt_example.exists():
            with open(txt_example, 'w', encoding='utf-8') as f:
                f.write("""# AI Image Generation Prompts
# One prompt per line, lines starting with # are comments

A beautiful sunset over mountains, photorealistic, 4K
Cute cat wearing a wizard hat, digital art style
Futuristic city skyline at night, cyberpunk aesthetic
Portrait of a wise old wizard, fantasy art
Abstract geometric patterns in blue and gold
""")
        
        # Example CSV file
        csv_example = self.prompts_dir / "example_prompts.csv"
        if not csv_example.exists():
            with open(csv_example, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'prompt', 'category', 'priority', 'parameters'])
                writer.writerow(['001', 'A majestic dragon flying over a castle', 'fantasy', '1', '{"style": "realistic", "quality": "high"}'])
                writer.writerow(['002', 'Modern minimalist living room interior', 'architecture', '2', '{"style": "clean", "lighting": "natural"}'])
                writer.writerow(['003', 'Portrait of a cyberpunk character', 'character', '1', '{"style": "neon", "mood": "dark"}'])
        
        # Example JSON file
        json_example = self.prompts_dir / "example_prompts.json"
        if not json_example.exists():
            prompts_data = {
                "prompts": [
                    {
                        "id": "json_001",
                        "text": "A serene Japanese garden with cherry blossoms",
                        "category": "nature",
                        "priority": 1,
                        "parameters": {
                            "style": "traditional",
                            "season": "spring",
                            "mood": "peaceful"
                        }
                    },
                    {
                        "id": "json_002", 
                        "text": "Steampunk airship flying through clouds",
                        "category": "steampunk",
                        "priority": 2,
                        "parameters": {
                            "style": "vintage",
                            "complexity": "detailed"
                        }
                    }
                ]
            }
            with open(json_example, 'w', encoding='utf-8') as f:
                json.dump(prompts_data, f, indent=2, ensure_ascii=False)
    
    def load_prompts_from_file(self, file_path: str) -> List[Prompt]:
        """Load prompts from various file formats"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.txt':
            return self._load_from_txt(file_path)
        elif extension == '.csv':
            return self._load_from_csv(file_path)
        elif extension == '.json':
            return self._load_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _load_from_txt(self, file_path: Path) -> List[Prompt]:
        """Load prompts from TXT file"""
        prompts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                prompt = Prompt(
                    id=f"txt_{file_path.stem}_{i:03d}",
                    text=line,
                    category=file_path.stem,
                    created_at=datetime.now().isoformat()
                )
                prompts.append(prompt)
        
        return prompts
    
    def _load_from_csv(self, file_path: Path) -> List[Prompt]:
        """Load prompts from CSV file"""
        prompts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Parse parameters if present
                parameters = {}
                if 'parameters' in row and row['parameters']:
                    try:
                        parameters = json.loads(row['parameters'])
                    except json.JSONDecodeError:
                        parameters = {}
                
                prompt = Prompt(
                    id=row.get('id', f"csv_{len(prompts):03d}"),
                    text=row['prompt'],
                    category=row.get('category', 'default'),
                    priority=int(row.get('priority', 1)),
                    parameters=parameters,
                    created_at=datetime.now().isoformat()
                )
                prompts.append(prompt)
        
        return prompts
    
    def _load_from_json(self, file_path: Path) -> List[Prompt]:
        """Load prompts from JSON file"""
        prompts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        prompts_data = data.get('prompts', [])
        
        for prompt_data in prompts_data:
            prompt = Prompt(
                id=prompt_data.get('id', f"json_{len(prompts):03d}"),
                text=prompt_data['text'],
                category=prompt_data.get('category', 'default'),
                priority=prompt_data.get('priority', 1),
                parameters=prompt_data.get('parameters', {}),
                created_at=datetime.now().isoformat()
            )
            prompts.append(prompt)
        
        return prompts
    
    def save_result(self, result: GenerationResult) -> str:
        """Save generation result with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save metadata
        metadata_file = self.results_dir / "metadata" / f"{result.prompt_id}_{timestamp}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        
        # Log result
        log_file = self.logs_dir / f"generation_log_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(log_file, 'a', encoding='utf-8') as f:
            status = "SUCCESS" if result.success else "FAILED"
            f.write(f"[{result.timestamp}] {status} - {result.prompt_id}\n")
            if result.error:
                f.write(f"  Error: {result.error}\n")
            if result.image_paths:
                f.write(f"  Images: {', '.join(result.image_paths)}\n")
            f.write("\n")
        
        return str(metadata_file)
    
    def get_pending_prompts(self, prompts: List[Prompt]) -> List[Prompt]:
        """Get prompts that are pending processing"""
        return [p for p in prompts if p.status == "pending"]
    
    def update_prompt_status(self, prompt: Prompt, status: str, error: str = None):
        """Update prompt status"""
        prompt.status = status
        prompt.processed_at = datetime.now().isoformat()
        if error:
            prompt.error = error
    
    def list_prompt_files(self) -> List[Dict[str, Any]]:
        """List all available prompt files"""
        files = []
        
        for file_path in self.prompts_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.csv', '.json']:
                try:
                    prompts = self.load_prompts_from_file(str(file_path))
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "format": file_path.suffix.lower()[1:],
                        "prompt_count": len(prompts),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "format": file_path.suffix.lower()[1:],
                        "prompt_count": 0,
                        "error": str(e)
                    })
        
        return files
