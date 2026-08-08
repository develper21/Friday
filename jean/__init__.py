"""
Jarvis compatibility module for desktop app imports.
This module provides backward compatibility for the desktop app.
"""

from assistance.daemon import VoiceAssistantDaemon

def get_version():
    """Get version information"""
    return "1.0.0"

__all__ = ['get_version', 'VoiceAssistantDaemon']
