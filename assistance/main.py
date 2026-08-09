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
from assistance.utils.logger import logger


def main():
    """Main entry point"""
    logger.header("Voice Assistant (Refactored Architecture)", 60)
    
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load()
    logger.success("Configuration loaded successfully")
    
    # Create and run daemon with new architecture
    daemon = VoiceAssistantDaemonRefactored(config)
    daemon.run()


if __name__ == "__main__":
    main()
