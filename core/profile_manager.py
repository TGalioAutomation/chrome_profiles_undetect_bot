import os
import json
import shutil
import sqlite3
import glob
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from config import PROFILES_DIR, DATABASE_URL


class ProfileStatus(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class ChromeProfile:
    """Chrome profile data structure"""
    name: str
    display_name: str
    user_agent: str
    proxy: Optional[str] = None
    window_size: tuple = (1920, 1080)
    headless: bool = False
    created_at: str = None
    last_used: str = None
    status: ProfileStatus = ProfileStatus.INACTIVE
    custom_options: List[str] = None
    notes: str = ""
    # Gmail account fields
    gmail_email: Optional[str] = None
    gmail_password: Optional[str] = None
    gmail_recovery_email: Optional[str] = None
    gmail_phone: Optional[str] = None
    gmail_2fa_secret: Optional[str] = None
    gmail_auto_login: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.custom_options is None:
            self.custom_options = []


class ProfileManager:
    """
    Manager for Chrome profiles with database storage and file management
    """
    
    def __init__(self):
        self.db_path = DATABASE_URL.replace("sqlite:///", "")
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for profile management"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    name TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    proxy TEXT,
                    window_width INTEGER DEFAULT 1920,
                    window_height INTEGER DEFAULT 1080,
                    headless BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    status TEXT DEFAULT 'inactive',
                    custom_options TEXT,
                    notes TEXT DEFAULT '',
                    gmail_email TEXT,
                    gmail_password TEXT,
                    gmail_recovery_email TEXT,
                    gmail_phone TEXT,
                    gmail_2fa_secret TEXT,
                    gmail_auto_login BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profile_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration INTEGER,
                    pages_visited INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (profile_name) REFERENCES profiles (name)
                )
            ''')
            
            # Add Gmail columns if they don't exist (migration)
            self._migrate_gmail_columns(cursor)

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def _migrate_gmail_columns(self, cursor):
        """Add Gmail columns to existing profiles table"""
        gmail_columns = [
            ('gmail_email', 'TEXT'),
            ('gmail_password', 'TEXT'),
            ('gmail_recovery_email', 'TEXT'),
            ('gmail_phone', 'TEXT'),
            ('gmail_2fa_secret', 'TEXT'),
            ('gmail_auto_login', 'BOOLEAN DEFAULT FALSE')
        ]

        for column_name, column_type in gmail_columns:
            try:
                cursor.execute(f'ALTER TABLE profiles ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                # Column already exists
                pass
    
    def create_profile(self, profile: ChromeProfile) -> bool:
        """Create a new Chrome profile"""
        try:
            # Check if profile already exists
            if self.profile_exists(profile.name):
                raise ValueError(f"Profile '{profile.name}' already exists")
            
            # Create profile directory
            profile_path = PROFILES_DIR / profile.name
            profile_path.mkdir(exist_ok=True)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO profiles (
                    name, display_name, user_agent, proxy,
                    window_width, window_height, headless,
                    created_at, status, custom_options, notes,
                    gmail_email, gmail_password, gmail_recovery_email,
                    gmail_phone, gmail_2fa_secret, gmail_auto_login
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.name,
                profile.display_name,
                profile.user_agent,
                profile.proxy,
                profile.window_size[0],
                profile.window_size[1],
                profile.headless,
                profile.created_at,
                profile.status.value,
                json.dumps(profile.custom_options),
                profile.notes,
                profile.gmail_email,
                profile.gmail_password,
                profile.gmail_recovery_email,
                profile.gmail_phone,
                profile.gmail_2fa_secret,
                profile.gmail_auto_login
            ))
            
            conn.commit()
            conn.close()
            
            # Save profile metadata
            self._save_profile_metadata(profile)
            
            return True
            
        except Exception as e:
            print(f"Error creating profile: {e}")
            return False
    
    def _save_profile_metadata(self, profile: ChromeProfile):
        """Save profile metadata to JSON file"""
        profile_path = PROFILES_DIR / profile.name
        metadata_file = profile_path / "metadata.json"
        
        try:
            metadata = asdict(profile)
            metadata['status'] = profile.status.value
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving profile metadata: {e}")
    
    def get_profile(self, name: str) -> Optional[ChromeProfile]:
        """Get profile by name"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM profiles WHERE name = ?', (name,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ChromeProfile(
                    name=row[0],
                    display_name=row[1],
                    user_agent=row[2],
                    proxy=row[3],
                    window_size=(row[4], row[5]),
                    headless=bool(row[6]),
                    created_at=row[7],
                    last_used=row[8],
                    status=ProfileStatus(row[9]),
                    custom_options=json.loads(row[10]) if row[10] else [],
                    notes=row[11] or ""
                )
            
            return None
            
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    def list_profiles(self) -> List[ChromeProfile]:
        """List all profiles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM profiles ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            profiles = []
            for row in rows:
                profile = ChromeProfile(
                    name=row[0],
                    display_name=row[1],
                    user_agent=row[2],
                    proxy=row[3],
                    window_size=(row[4], row[5]),
                    headless=bool(row[6]),
                    created_at=row[7],
                    last_used=row[8],
                    status=ProfileStatus(row[9]),
                    custom_options=json.loads(row[10]) if row[10] else [],
                    notes=row[11] or ""
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"Error listing profiles: {e}")
            return []
    
    def update_profile(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update profile with new data"""
        try:
            if not self.profile_exists(name):
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'window_size':
                    set_clauses.extend(['window_width = ?', 'window_height = ?'])
                    values.extend([value[0], value[1]])
                elif key == 'custom_options':
                    set_clauses.append('custom_options = ?')
                    values.append(json.dumps(value))
                elif key == 'status':
                    set_clauses.append('status = ?')
                    values.append(value.value if isinstance(value, ProfileStatus) else value)
                else:
                    set_clauses.append(f'{key} = ?')
                    values.append(value)
            
            if set_clauses:
                query = f"UPDATE profiles SET {', '.join(set_clauses)} WHERE name = ?"
                values.append(name)
                cursor.execute(query, values)
                conn.commit()
            
            conn.close()
            
            # Update metadata file
            profile = self.get_profile(name)
            if profile:
                self._save_profile_metadata(profile)
            
            return True
            
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False
    
    def delete_profile(self, name: str, delete_files: bool = True) -> bool:
        """Delete profile from database and optionally delete files"""
        try:
            if not self.profile_exists(name):
                return False
            
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM profile_sessions WHERE profile_name = ?', (name,))
            cursor.execute('DELETE FROM profiles WHERE name = ?', (name,))
            
            conn.commit()
            conn.close()
            
            # Delete profile directory if requested
            if delete_files:
                profile_path = PROFILES_DIR / name
                if profile_path.exists():
                    shutil.rmtree(profile_path)
            
            return True
            
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False

    def get_system_chrome_profiles(self) -> List[Dict[str, Any]]:
        """Detect existing Chrome profiles on the system"""
        profiles = []

        # Common Chrome profile locations
        chrome_paths = [
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data"),  # Windows
            os.path.expanduser("~/Library/Application Support/Google/Chrome"),    # macOS
            os.path.expanduser("~/.config/google-chrome"),                       # Linux
            os.path.expanduser("~/.config/chromium"),                           # Chromium Linux
        ]

        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    profiles.extend(self._scan_chrome_directory(chrome_path))
                except Exception as e:
                    print(f"Error scanning {chrome_path}: {e}")

        return profiles

    def _scan_chrome_directory(self, chrome_path: str) -> List[Dict[str, Any]]:
        """Scan Chrome directory for profiles"""
        profiles = []

        # Look for profile directories
        profile_patterns = [
            "Default",
            "Profile *",
            "Person *"
        ]

        for pattern in profile_patterns:
            profile_dirs = glob.glob(os.path.join(chrome_path, pattern))

            for profile_dir in profile_dirs:
                if os.path.isdir(profile_dir):
                    profile_info = self._get_profile_info(profile_dir)
                    if profile_info:
                        profiles.append(profile_info)

        return profiles

    def _get_profile_info(self, profile_dir: str) -> Optional[Dict[str, Any]]:
        """Get information about a Chrome profile"""
        try:
            profile_name = os.path.basename(profile_dir)

            # Check if profile has essential files
            preferences_file = os.path.join(profile_dir, "Preferences")
            if not os.path.exists(preferences_file):
                return None

            # Read preferences to get profile info
            display_name = profile_name
            try:
                with open(preferences_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)

                    # Get profile display name
                    if 'profile' in prefs and 'name' in prefs['profile']:
                        display_name = prefs['profile']['name']

                    # Get account info if available
                    account_info = self._extract_account_info(prefs)

            except Exception as e:
                print(f"Warning: Could not read preferences for {profile_name}: {e}")
                account_info = {}

            # Get profile size
            profile_size = self._get_directory_size(profile_dir)

            # Check last modified time
            last_modified = datetime.fromtimestamp(os.path.getmtime(profile_dir)).isoformat()

            return {
                'name': profile_name,
                'display_name': display_name,
                'path': profile_dir,
                'size_mb': round(profile_size / (1024 * 1024), 2),
                'last_modified': last_modified,
                'account_info': account_info,
                'has_login_data': os.path.exists(os.path.join(profile_dir, "Login Data")),
                'has_cookies': os.path.exists(os.path.join(profile_dir, "Cookies")),
                'has_history': os.path.exists(os.path.join(profile_dir, "History"))
            }

        except Exception as e:
            print(f"Error getting profile info for {profile_dir}: {e}")
            return None

    def _extract_account_info(self, prefs: dict) -> Dict[str, Any]:
        """Extract account information from Chrome preferences"""
        account_info = {}

        try:
            # Try to get Google account info
            if 'account_info' in prefs:
                for account in prefs['account_info']:
                    if 'email' in account:
                        account_info['email'] = account['email']
                        break

            # Try alternative locations
            if 'signin' in prefs and 'allowed_username' in prefs['signin']:
                account_info['email'] = prefs['signin']['allowed_username']

        except Exception as e:
            print(f"Warning: Could not extract account info: {e}")

        return account_info

    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
        except Exception:
            pass
        return total_size

    def import_chrome_profile(self, source_path: str, profile_name: str, display_name: str = None) -> bool:
        """Import existing Chrome profile"""
        try:
            print(f"🔍 Starting import process...")
            print(f"   Source: {source_path}")
            print(f"   Profile name: {profile_name}")
            print(f"   Display name: {display_name}")

            # Validate inputs
            if not source_path or not profile_name:
                raise ValueError("Source path and profile name are required")

            # Check if source path exists
            if not os.path.exists(source_path):
                raise ValueError(f"Source profile path does not exist: {source_path}")

            # Check if source is a directory
            if not os.path.isdir(source_path):
                raise ValueError(f"Source path is not a directory: {source_path}")

            # Check if profile name already exists
            existing_profile = self.get_profile(profile_name)
            if existing_profile:
                raise ValueError(f"Profile '{profile_name}' already exists")

            # Validate profile name format
            if not profile_name.replace('_', '').replace('-', '').isalnum():
                raise ValueError("Profile name can only contain letters, numbers, hyphens, and underscores")

            # Create destination path
            dest_path = PROFILES_DIR / profile_name

            print(f"📥 Importing Chrome profile from {source_path} to {dest_path}")

            # Ensure PROFILES_DIR exists
            PROFILES_DIR.mkdir(exist_ok=True)

            # Remove destination if exists
            if dest_path.exists():
                print(f"🗑️ Removing existing destination: {dest_path}")
                shutil.rmtree(dest_path)

            # Copy profile directory with detailed logging
            print(f"📂 Copying profile directory...")
            try:
                shutil.copytree(source_path, dest_path)
                print(f"✅ Profile directory copied successfully")
            except Exception as copy_error:
                raise ValueError(f"Failed to copy profile directory: {str(copy_error)}")

            # Create profile entry in database
            print(f"💾 Creating database entry...")

            # Set created_at timestamp
            created_at = datetime.now().isoformat()

            profile = ChromeProfile(
                name=profile_name,
                display_name=display_name or profile_name,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                notes=f"Imported from system Chrome profile: {source_path}",
                created_at=created_at,
                custom_options=[]
            )

            # Save to database with detailed error handling
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                print(f"📝 Inserting profile into database...")

                cursor.execute('''
                    INSERT INTO profiles (
                        name, display_name, user_agent, proxy,
                        window_width, window_height, headless,
                        created_at, status, custom_options, notes,
                        gmail_email, gmail_password, gmail_recovery_email,
                        gmail_phone, gmail_2fa_secret, gmail_auto_login
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile.name,
                    profile.display_name,
                    profile.user_agent,
                    profile.proxy,
                    profile.window_size[0],
                    profile.window_size[1],
                    profile.headless,
                    profile.created_at,
                    profile.status.value,
                    json.dumps(profile.custom_options or []),
                    profile.notes,
                    profile.gmail_email,
                    profile.gmail_password,
                    profile.gmail_recovery_email,
                    profile.gmail_phone,
                    profile.gmail_2fa_secret,
                    profile.gmail_auto_login
                ))

                conn.commit()
                print(f"✅ Database entry created successfully")

            except sqlite3.Error as db_error:
                raise ValueError(f"Database error: {str(db_error)}")
            finally:
                if conn:
                    conn.close()

            print(f"🎉 Successfully imported profile: {profile_name}")
            return True

        except Exception as e:
            print(f"❌ Error importing profile: {e}")
            return False
    
    def profile_exists(self, name: str) -> bool:
        """Check if profile exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM profiles WHERE name = ?', (name,))
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            print(f"Error checking profile existence: {e}")
            return False
    
    def update_profile_status(self, name: str, status: ProfileStatus) -> bool:
        """Update profile status"""
        return self.update_profile(name, {'status': status})
    
    def update_last_used(self, name: str) -> bool:
        """Update profile last used timestamp"""
        return self.update_profile(name, {'last_used': datetime.now().isoformat()})
    
    def get_active_profiles(self) -> List[ChromeProfile]:
        """Get all active/running profiles"""
        profiles = self.list_profiles()
        return [p for p in profiles if p.status in [ProfileStatus.ACTIVE, ProfileStatus.RUNNING]]
    
    def start_session(self, profile_name: str) -> int:
        """Start a new session for profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO profile_sessions (profile_name, start_time, status)
                VALUES (?, ?, 'active')
            ''', (profile_name, datetime.now().isoformat()))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Update profile status
            self.update_profile_status(profile_name, ProfileStatus.RUNNING)
            self.update_last_used(profile_name)
            
            return session_id
            
        except Exception as e:
            print(f"Error starting session: {e}")
            return -1
    
    def end_session(self, session_id: int, pages_visited: int = 0) -> bool:
        """End a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session start time
            cursor.execute('SELECT start_time, profile_name FROM profile_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            
            if row:
                start_time = datetime.fromisoformat(row[0])
                profile_name = row[1]
                end_time = datetime.now()
                duration = int((end_time - start_time).total_seconds())
                
                cursor.execute('''
                    UPDATE profile_sessions 
                    SET end_time = ?, duration = ?, pages_visited = ?, status = 'completed'
                    WHERE id = ?
                ''', (end_time.isoformat(), duration, pages_visited, session_id))
                
                conn.commit()
                
                # Update profile status back to inactive
                self.update_profile_status(profile_name, ProfileStatus.INACTIVE)
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error ending session: {e}")
            return False
