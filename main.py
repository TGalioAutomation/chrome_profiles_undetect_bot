#!/usr/bin/env python3
"""
Chrome Profiles Manager - Bot Bypass & Multi-Profile Management Tool

Main application entry point for the Chrome profiles management system
with advanced bot detection bypass capabilities.

Author: Chrome Profiles Manager Team
Version: 1.0.0
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.routes import BrowserAPI
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL, LOG_FORMAT


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log', encoding='utf-8')
        ]
    )


def main():
    """Main application entry point"""
    print("=" * 60)
    print("🚀 Chrome Profiles Manager - Bot Bypass Tool")
    print("=" * 60)
    print()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Create and configure the API
        api = BrowserAPI()

        logger.info("Starting Chrome Profiles Manager...")
        logger.info(f"Server will be available at: http://{FLASK_HOST}:{FLASK_PORT}")

        print(f"🌐 Web Interface: http://{FLASK_HOST}:{FLASK_PORT}")
        print(f"📊 Dashboard: http://{FLASK_HOST}:{FLASK_PORT}/")
        print(f"👥 Profiles: http://{FLASK_HOST}:{FLASK_PORT}/profiles")
        print()
        print("Features:")
        print("✅ Multi-profile Chrome management")
        print("✅ Advanced bot detection bypass")
        print("✅ Proxy support")
        print("✅ User agent rotation")
        print("✅ Canvas & WebGL fingerprinting bypass")
        print("✅ Real-time browser control")
        print("✅ Web-based management interface")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)

        # Run the Flask application
        api.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n👋 Server stopped. Goodbye!")

    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
