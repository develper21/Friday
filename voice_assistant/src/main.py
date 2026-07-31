#!/usr/bin/env python3
"""
Voice Assistant - Main Entry Point
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from daemon import VoiceAssistantDaemon
from config.settings import ConfigLoader


def main():
    """Main entry point"""
    print("🎙️  Voice Assistant")
    print("="*60)
    
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    # Create and run daemon
    daemon = VoiceAssistantDaemon(config)
    daemon.run()


if __name__ == "__main__":
    main()
