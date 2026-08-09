#!/usr/bin/env python3
"""
Voice Assistant - Main Entry Point
"""

import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from assistance.daemon import VoiceAssistantDaemonRefactored
from assistance.config.settings import ConfigLoader


def main():
    """Main entry point"""
    print("🎙️  Voice Assistant (Refactored Architecture)")
    print("="*60)
    
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    # Create and run daemon with new architecture
    daemon = VoiceAssistantDaemonRefactored(config)
    daemon.run()


if __name__ == "__main__":
    main()
