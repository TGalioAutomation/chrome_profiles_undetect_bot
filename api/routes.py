from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import threading
import time
from typing import Dict, Any, Optional

from core.profile_manager import ProfileManager, ChromeProfile, ProfileStatus
from core.chrome_driver import ChromeDriverManager
from core.bot_bypass import BotBypassManager


class BrowserAPI:
    """
    REST API for managing Chrome profiles and browsers
    """
    
    def __init__(self):
        self.app = Flask(__name__, template_folder='../ui/templates', static_folder='../ui/static')
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.profile_manager = ProfileManager()
        self.active_drivers: Dict[str, ChromeDriverManager] = {}
        self.active_sessions: Dict[str, int] = {}
        self.multi_thread_generators = {}  # Track multi-thread generators
        
        self._setup_routes()
        self._setup_socketio_events()
        self._setup_error_handlers()
    
    def _setup_routes(self):
        """Setup REST API routes"""
        
        # Web UI routes
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/profiles')
        def profiles_page():
            return render_template('profiles.html')
        
        # API routes
        @self.app.route('/api/profiles', methods=['GET'])
        def get_profiles():
            """Get all profiles"""
            try:
                profiles = self.profile_manager.list_profiles()
                profiles_data = []
                
                for profile in profiles:
                    profile_data = {
                        'name': profile.name,
                        'display_name': profile.display_name,
                        'user_agent': profile.user_agent,
                        'proxy': profile.proxy,
                        'window_size': profile.window_size,
                        'headless': profile.headless,
                        'created_at': profile.created_at,
                        'last_used': profile.last_used,
                        'status': profile.status.value,
                        'notes': profile.notes,
                        'is_running': profile.name in self.active_drivers
                    }
                    profiles_data.append(profile_data)
                
                return jsonify({
                    'success': True,
                    'profiles': profiles_data
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles', methods=['POST'])
        def create_profile():
            """Create new profile"""
            try:
                # Debug: Print request info
                print(f"Content-Type: {request.content_type}")
                print(f"Request data: {request.data}")

                # Handle JSON parsing with better error handling
                try:
                    data = request.get_json(force=True)
                except Exception as json_error:
                    print(f"JSON parsing error: {json_error}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid JSON data: {str(json_error)}'
                    }), 400

                print(f"Parsed JSON: {data}")

                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No JSON data received'
                    }), 400

                # Validate required fields
                if 'name' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Profile name is required'
                    }), 400

                if 'user_agent' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'User agent is required'
                    }), 400

                profile = ChromeProfile(
                    name=data['name'],
                    display_name=data.get('display_name', data['name']),
                    user_agent=data['user_agent'],
                    proxy=data.get('proxy'),
                    window_size=tuple(data.get('window_size', [1920, 1080])),
                    headless=data.get('headless', False),
                    custom_options=data.get('custom_options', []),
                    notes=data.get('notes', ''),
                    # Gmail account fields
                    gmail_email=data.get('gmail_email'),
                    gmail_password=data.get('gmail_password'),
                    gmail_recovery_email=data.get('gmail_recovery_email'),
                    gmail_phone=data.get('gmail_phone'),
                    gmail_2fa_secret=data.get('gmail_2fa_secret'),
                    gmail_auto_login=data.get('gmail_auto_login', False)
                )

                success = self.profile_manager.create_profile(profile)

                if success:
                    self._emit_profile_update()
                    return jsonify({
                        'success': True,
                        'message': f'Profile {profile.name} created successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to create profile'
                    }), 400

            except ValueError as e:
                # Handle profile already exists or validation errors
                print(f"Validation error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            except KeyError as e:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {str(e)}'
                }), 400
            except Exception as e:
                print(f"Error creating profile: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles/<profile_name>', methods=['GET'])
        def get_profile(profile_name):
            """Get specific profile"""
            try:
                profile = self.profile_manager.get_profile(profile_name)
                
                if profile:
                    return jsonify({
                        'success': True,
                        'profile': {
                            'name': profile.name,
                            'display_name': profile.display_name,
                            'user_agent': profile.user_agent,
                            'proxy': profile.proxy,
                            'window_size': profile.window_size,
                            'headless': profile.headless,
                            'created_at': profile.created_at,
                            'last_used': profile.last_used,
                            'status': profile.status.value,
                            'notes': profile.notes,
                            'is_running': profile_name in self.active_drivers
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Profile not found'
                    }), 404
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles/<profile_name>', methods=['PUT'])
        def update_profile(profile_name):
            """Update profile"""
            try:
                data = request.get_json()
                success = self.profile_manager.update_profile(profile_name, data)
                
                if success:
                    self._emit_profile_update()
                    return jsonify({
                        'success': True,
                        'message': f'Profile {profile_name} updated successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to update profile'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles/<profile_name>', methods=['DELETE'])
        def delete_profile(profile_name):
            """Delete profile"""
            try:
                # Stop browser if running
                if profile_name in self.active_drivers:
                    self.stop_browser(profile_name)
                
                success = self.profile_manager.delete_profile(profile_name, delete_files=True)
                
                if success:
                    self._emit_profile_update()
                    return jsonify({
                        'success': True,
                        'message': f'Profile {profile_name} deleted successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to delete profile'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles/<profile_name>/start', methods=['POST'])
        def start_browser(profile_name):
            """Start browser for profile"""
            try:
                if profile_name in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser already running for this profile'
                    }), 400
                
                profile = self.profile_manager.get_profile(profile_name)
                if not profile:
                    return jsonify({
                        'success': False,
                        'error': 'Profile not found'
                    }), 404
                
                # Start browser in background thread
                thread = threading.Thread(
                    target=self._start_browser_thread,
                    args=(profile_name, profile)
                )
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'success': True,
                    'message': f'Starting browser for profile {profile_name}'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles/<profile_name>/stop', methods=['POST'])
        def stop_browser_route(profile_name):
            """Stop browser for profile"""
            try:
                success = self.stop_browser(profile_name)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Browser stopped for profile {profile_name}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/profiles/<profile_name>/navigate', methods=['POST'])
        def navigate_browser(profile_name):
            """Navigate browser to URL"""
            try:
                data = request.get_json()
                url = data.get('url')
                
                if not url:
                    return jsonify({
                        'success': False,
                        'error': 'URL is required'
                    }), 400
                
                if profile_name not in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400
                
                driver_manager = self.active_drivers[profile_name]
                driver_manager.navigate_to(url)
                
                return jsonify({
                    'success': True,
                    'message': f'Navigated to {url}'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/profiles/<profile_name>/window-position', methods=['POST'])
        def set_window_position(profile_name):
            """Set browser window position and size"""
            try:
                data = request.get_json()
                x = data.get('x', 0)
                y = data.get('y', 0)
                width = data.get('width', 1024)
                height = data.get('height', 768)

                if profile_name not in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400

                driver_manager = self.active_drivers[profile_name]

                # Set window position and size
                driver_manager.driver.set_window_position(x, y)
                driver_manager.driver.set_window_size(width, height)

                return jsonify({
                    'success': True,
                    'message': f'Window positioned at ({x}, {y}) with size {width}x{height}'
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/profiles/<profile_name>/gmail-login', methods=['POST'])
        def gmail_auto_login(profile_name):
            """Auto-login to Gmail for profile"""
            try:
                if profile_name not in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400

                # Get profile data for Gmail credentials
                profile = self.profile_manager.get_profile(profile_name)
                if not profile or not profile.gmail_email:
                    return jsonify({
                        'success': False,
                        'error': 'No Gmail account configured for this profile'
                    }), 400

                driver_manager = self.active_drivers[profile_name]

                # Perform auto-login
                success = driver_manager.auto_login_gmail(
                    email=profile.gmail_email,
                    password=profile.gmail_password,
                    recovery_email=profile.gmail_recovery_email,
                    phone=profile.gmail_phone,
                    tfa_secret=profile.gmail_2fa_secret
                )

                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Gmail auto-login successful for {profile.gmail_email}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Gmail auto-login failed'
                    }), 400

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/system-profiles', methods=['GET'])
        def get_system_chrome_profiles():
            """Get existing Chrome profiles from system"""
            try:
                print(f"🔍 Scanning for system Chrome profiles...")
                profiles = self.profile_manager.get_system_chrome_profiles()
                print(f"📊 Found {len(profiles)} profiles")

                return jsonify({
                    'success': True,
                    'profiles': profiles,
                    'count': len(profiles)
                })

            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error scanning system profiles: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500

        @self.app.route('/api/import-profile', methods=['POST'])
        def import_chrome_profile():
            """Import existing Chrome profile"""
            try:
                print(f"🔍 Import profile API called")

                data = request.get_json()
                print(f"📊 Request data: {data}")

                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400

                source_path = data.get('source_path')
                profile_name = data.get('profile_name')
                display_name = data.get('display_name')

                print(f"📝 Import parameters:")
                print(f"   Source path: {source_path}")
                print(f"   Profile name: {profile_name}")
                print(f"   Display name: {display_name}")

                if not source_path or not profile_name:
                    error_msg = 'source_path and profile_name are required'
                    print(f"❌ Validation error: {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400

                print(f"🚀 Starting import process...")

                success = self.profile_manager.import_chrome_profile(
                    source_path=source_path,
                    profile_name=profile_name,
                    display_name=display_name
                )

                if success:
                    print(f"✅ Import successful, emitting update...")
                    self._emit_profile_update()
                    return jsonify({
                        'success': True,
                        'message': f'Profile {profile_name} imported successfully'
                    })
                else:
                    error_msg = 'Import function returned False'
                    print(f"❌ Import failed: {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400

            except ValueError as ve:
                error_msg = str(ve)
                print(f"❌ Validation error: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Unexpected error: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500

        @self.app.route('/api/profiles/<profile_name>/test-gmail', methods=['POST'])
        def test_gmail_access(profile_name):
            """Test Gmail access for profile"""
            try:
                if profile_name not in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400

                driver_manager = self.active_drivers[profile_name]

                # Test Gmail access with force check
                gmail_accessible = driver_manager.test_gmail_access()

                # If first check fails, try force check
                if not gmail_accessible:
                    print(f"🔄 First Gmail check failed, trying force check...")
                    gmail_accessible = driver_manager.force_gmail_login_check()

                return jsonify({
                    'success': True,
                    'gmail_accessible': gmail_accessible,
                    'message': 'Gmail accessible' if gmail_accessible else 'Gmail not accessible - manual login required'
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/scripts', methods=['GET'])
        def list_scripts():
            """List all available Selenium scripts"""
            try:
                # Get scripts from any active driver (they all have the same script manager)
                if self.active_drivers:
                    driver_manager = next(iter(self.active_drivers.values()))
                    scripts = driver_manager.list_available_scripts()
                else:
                    # Create temporary script manager
                    from core.script_manager import SeleniumScriptManager
                    script_manager = SeleniumScriptManager()
                    scripts = [
                        {
                            "name": script.name,
                            "display_name": script.display_name,
                            "description": script.description,
                            "file_path": script.file_path,
                            "created_at": script.created_at
                        }
                        for script in script_manager.list_scripts()
                    ]

                return jsonify({
                    'success': True,
                    'scripts': scripts,
                    'count': len(scripts)
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/profiles/<profile_name>/execute-script', methods=['POST'])
        def execute_script(profile_name):
            """Execute Selenium script on profile"""
            try:
                if profile_name not in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400

                data = request.get_json()
                if not data or 'script_name' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'script_name is required'
                    }), 400

                script_name = data['script_name']
                script_params = data.get('parameters', {})

                print(f"🚀 Executing script {script_name} on profile {profile_name}")
                print(f"📊 Parameters: {script_params}")

                driver_manager = self.active_drivers[profile_name]
                result = driver_manager.execute_script(script_name, **script_params)

                return jsonify(result)

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/prompt-files', methods=['GET'])
        def list_prompt_files():
            """List available prompt files"""
            try:
                # Get prompt files from any active driver
                if self.active_drivers:
                    driver_manager = next(iter(self.active_drivers.values()))
                    files = driver_manager.list_prompt_files()
                else:
                    # Create temporary prompt manager
                    from core.prompt_manager import PromptManager
                    prompt_manager = PromptManager()
                    files = prompt_manager.list_prompt_files()

                return jsonify({
                    'success': True,
                    'files': files,
                    'count': len(files)
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/profiles/<profile_name>/ai-generation', methods=['POST'])
        def run_ai_generation(profile_name):
            """Run AI image generation batch (single-threaded)"""
            try:
                if profile_name not in self.active_drivers:
                    return jsonify({
                        'success': False,
                        'error': 'Browser not running for this profile'
                    }), 400

                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400

                prompt_file = data.get('prompt_file')
                platform = data.get('platform', 'stable_diffusion')
                generation_params = data.get('parameters', {})

                if not prompt_file:
                    return jsonify({
                        'success': False,
                        'error': 'prompt_file is required'
                    }), 400

                print(f"🚀 Starting AI generation batch for profile {profile_name}")
                print(f"📊 Parameters: {data}")

                driver_manager = self.active_drivers[profile_name]
                result = driver_manager.run_ai_generation_batch(
                    prompt_file=prompt_file,
                    platform=platform,
                    **generation_params
                )

                return jsonify(result)

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/ai-generation-multi', methods=['POST'])
        def run_multi_thread_generation():
            """Run multi-threaded AI image generation"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400

                prompt_file = data.get('prompt_file')
                platform = data.get('platform', 'stable_diffusion')
                profile_names = data.get('profiles', [])
                thread_config = data.get('thread_config', {})
                generation_params = data.get('parameters', {})

                if not prompt_file:
                    return jsonify({
                        'success': False,
                        'error': 'prompt_file is required'
                    }), 400

                if not profile_names:
                    return jsonify({
                        'success': False,
                        'error': 'At least one profile is required'
                    }), 400

                # Validate profiles are running
                available_drivers = []
                for profile_name in profile_names:
                    if profile_name in self.active_drivers:
                        available_drivers.append(self.active_drivers[profile_name])
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Profile {profile_name} is not running'
                        }), 400

                print(f"🚀 Starting multi-threaded AI generation")
                print(f"📊 Profiles: {profile_names}")
                print(f"📊 Platform: {platform}")
                print(f"📊 Prompt file: {prompt_file}")

                # Load prompts
                from core.prompt_manager import PromptManager
                prompt_manager = PromptManager()
                prompts = prompt_manager.load_prompts_from_file(prompt_file)
                pending_prompts = prompt_manager.get_pending_prompts(prompts)

                if not pending_prompts:
                    return jsonify({
                        'success': True,
                        'message': 'No pending prompts to process',
                        'data': {'total_prompts': len(prompts), 'pending_prompts': 0}
                    })

                # Create thread configuration
                from core.thread_manager import ThreadConfig, MultiThreadGenerator
                config = ThreadConfig(
                    max_workers=thread_config.get('max_workers', len(available_drivers)),
                    timeout=thread_config.get('timeout', 300),
                    retry_attempts=thread_config.get('retry_attempts', 2),
                    delay_between_batches=thread_config.get('delay_between_batches', 1.0)
                )

                # Create multi-thread generator
                generator = MultiThreadGenerator(self.profile_manager, config)

                # Set up progress callback
                def progress_callback(progress):
                    # Emit progress via WebSocket
                    self.socketio.emit('generation_progress', {
                        'total': progress.total_prompts,
                        'completed': progress.completed,
                        'successful': progress.successful,
                        'failed': progress.failed,
                        'progress_percentage': progress.progress_percentage,
                        'elapsed_time': progress.elapsed_time,
                        'estimated_remaining': progress.estimated_remaining
                    })

                generator.set_progress_callback(progress_callback)

                # Start generation
                batch_id = generator.start_batch_generation(
                    prompts=pending_prompts,
                    platform=platform,
                    drivers=available_drivers,
                    **generation_params
                )

                # Store generator for tracking
                self.multi_thread_generators[batch_id] = generator

                return jsonify({
                    'success': True,
                    'message': f'Multi-threaded generation started',
                    'data': {
                        'batch_id': batch_id,
                        'total_prompts': len(pending_prompts),
                        'workers': config.max_workers,
                        'profiles': profile_names
                    }
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/ai-generation-progress/<batch_id>', methods=['GET'])
        def get_generation_progress(batch_id):
            """Get progress of multi-threaded generation"""
            try:
                if batch_id not in self.multi_thread_generators:
                    return jsonify({
                        'success': False,
                        'error': 'Batch not found'
                    }), 404

                generator = self.multi_thread_generators[batch_id]
                progress = generator.get_progress()

                return jsonify({
                    'success': True,
                    'progress': {
                        'batch_id': batch_id,
                        'total_prompts': progress.total_prompts,
                        'completed': progress.completed,
                        'successful': progress.successful,
                        'failed': progress.failed,
                        'in_progress': progress.in_progress,
                        'progress_percentage': progress.progress_percentage,
                        'elapsed_time': progress.elapsed_time,
                        'estimated_remaining': progress.estimated_remaining,
                        'is_running': generator.is_generation_running()
                    }
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/ai-generation-stop/<batch_id>', methods=['POST'])
        def stop_generation(batch_id):
            """Stop multi-threaded generation"""
            try:
                if batch_id not in self.multi_thread_generators:
                    return jsonify({
                        'success': False,
                        'error': 'Batch not found'
                    }), 404

                generator = self.multi_thread_generators[batch_id]
                generator.stop_generation()

                # Remove from tracking
                del self.multi_thread_generators[batch_id]

                return jsonify({
                    'success': True,
                    'message': 'Generation stopped'
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/generation-stats', methods=['GET'])
        def get_generation_stats():
            """Get AI generation statistics"""
            try:
                # Get stats from any active driver
                if self.active_drivers:
                    driver_manager = next(iter(self.active_drivers.values()))
                    stats = driver_manager.get_generation_stats()
                else:
                    # Create temporary stats
                    from pathlib import Path
                    results_dir = Path("results")
                    stats = {
                        "total_images": 0,
                        "total_metadata": 0,
                        "total_logs": 0,
                        "results_dir_size": 0
                    }

                    if results_dir.exists():
                        images_dir = results_dir / "images"
                        metadata_dir = results_dir / "metadata"
                        logs_dir = Path("logs")

                        stats.update({
                            "total_images": len(list(images_dir.glob("*"))) if images_dir.exists() else 0,
                            "total_metadata": len(list(metadata_dir.glob("*"))) if metadata_dir.exists() else 0,
                            "total_logs": len(list(logs_dir.glob("*"))) if logs_dir.exists() else 0
                        })

                return jsonify({
                    'success': True,
                    'stats': stats
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get system status"""
            try:
                active_profiles = list(self.active_drivers.keys())
                total_profiles = len(self.profile_manager.list_profiles())
                
                return jsonify({
                    'success': True,
                    'status': {
                        'total_profiles': total_profiles,
                        'active_browsers': len(active_profiles),
                        'active_profiles': active_profiles
                    }
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def _setup_socketio_events(self):
        """Setup WebSocket events"""

        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected')
            emit('status', {'message': 'Connected to server'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')

    def _setup_error_handlers(self):
        """Setup global error handlers"""

        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                'success': False,
                'error': 'Bad Request: ' + str(error.description)
            }), 400

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Not Found: ' + str(error.description)
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            print(f"Internal server error: {error}")
            return jsonify({
                'success': False,
                'error': 'Internal Server Error'
            }), 500

        @self.app.errorhandler(Exception)
        def handle_exception(error):
            print(f"Unhandled exception: {error}")
            return jsonify({
                'success': False,
                'error': f'Server Error: {str(error)}'
            }), 500
    
    def _start_browser_thread(self, profile_name: str, profile: ChromeProfile):
        """Start browser in background thread"""
        try:
            # Create driver manager
            driver_manager = ChromeDriverManager(profile_name)
            
            # Start driver with profile settings
            driver = driver_manager.start_driver(
                headless=profile.headless,
                proxy=profile.proxy,
                user_agent=profile.user_agent,
                window_size=profile.window_size,
                custom_options=profile.custom_options
            )
            
            # Apply bot bypass techniques
            bypass_manager = BotBypassManager(driver)
            bypass_manager.apply_all_bypasses()
            
            # Store active driver
            self.active_drivers[profile_name] = driver_manager
            
            # Start session
            session_id = self.profile_manager.start_session(profile_name)
            self.active_sessions[profile_name] = session_id

            # Auto-login to Gmail if configured
            if profile.gmail_auto_login and profile.gmail_email and profile.gmail_password:
                try:
                    print(f"🔐 Auto-logging into Gmail for profile: {profile_name}")
                    success = driver_manager.auto_login_gmail(
                        email=profile.gmail_email,
                        password=profile.gmail_password,
                        recovery_email=profile.gmail_recovery_email,
                        phone=profile.gmail_phone,
                        tfa_secret=profile.gmail_2fa_secret
                    )
                    if success:
                        print(f"✅ Gmail auto-login successful for {profile_name}")
                    else:
                        print(f"❌ Gmail auto-login failed for {profile_name}")
                except Exception as e:
                    print(f"❌ Gmail auto-login error for {profile_name}: {e}")

            # Emit status update
            self._emit_browser_started(profile_name)

            print(f"Browser started for profile: {profile_name}")
            
        except Exception as e:
            print(f"Error starting browser for {profile_name}: {e}")
            self._emit_browser_error(profile_name, str(e))
    
    def stop_browser(self, profile_name: str) -> bool:
        """Stop browser for profile"""
        try:
            if profile_name in self.active_drivers:
                driver_manager = self.active_drivers[profile_name]
                driver_manager.quit_driver()
                del self.active_drivers[profile_name]
                
                # End session
                if profile_name in self.active_sessions:
                    session_id = self.active_sessions[profile_name]
                    self.profile_manager.end_session(session_id)
                    del self.active_sessions[profile_name]
                
                # Emit status update
                self._emit_browser_stopped(profile_name)
                
                print(f"Browser stopped for profile: {profile_name}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error stopping browser for {profile_name}: {e}")
            return False
    
    def _emit_profile_update(self):
        """Emit profile list update to clients"""
        self.socketio.emit('profiles_updated')
    
    def _emit_browser_started(self, profile_name: str):
        """Emit browser started event"""
        self.socketio.emit('browser_started', {'profile': profile_name})
    
    def _emit_browser_stopped(self, profile_name: str):
        """Emit browser stopped event"""
        self.socketio.emit('browser_stopped', {'profile': profile_name})
    
    def _emit_browser_error(self, profile_name: str, error: str):
        """Emit browser error event"""
        self.socketio.emit('browser_error', {'profile': profile_name, 'error': error})
    
    def run(self, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=False):
        """Run the Flask application"""
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=allow_unsafe_werkzeug)
