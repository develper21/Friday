"""
Command Parser
Parses voice commands and extracts intents and entities
"""

from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


class Intent(Enum):
    """Command intents"""
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    CLOSE_ALL_APPS = "close_all_apps"
    CLOSE_ALL_TABS = "close_all_tabs"
    POWER_OFF = "power_off"
    RESTART = "restart"
    WEATHER = "weather"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Parsed command result"""
    intent: Intent
    entity: Optional[str] = None
    confidence: float = 1.0


class CommandParser:
    def __init__(self):
        """Initialize command parser"""
        # Intent keywords
        self.intent_patterns = {
            Intent.OPEN_APP: ["open", "launch", "start", "run"],
            Intent.CLOSE_APP: ["close", "quit", "exit", "kill"],
            Intent.CLOSE_ALL_APPS: ["close all app", "close all application", "quit all"],
            Intent.CLOSE_ALL_TABS: ["close all tab", "close all browser", "close tab"],
            Intent.POWER_OFF: ["shut down", "power off", "turn off", "shutdown"],
            Intent.RESTART: ["restart", "reboot", "restart system"],
            Intent.WEATHER: ["weather", "temperature", "forecast", "how is the weather", "what's the weather", "current weather"]
        }
        
    def parse(self, text: str) -> ParsedCommand:
        """
        Parse voice command text
        
        Args:
            text: Transcribed text
            
        Returns:
            ParsedCommand with intent and entity
        """
        text = text.lower().strip()
        
        # Detect intent
        intent = self._detect_intent(text)
        
        # Extract entity (app name)
        entity = self._extract_entity(text, intent)
        
        return ParsedCommand(intent=intent, entity=entity)
    
    def _detect_intent(self, text: str) -> Intent:
        """Detect intent from text"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return intent
        return Intent.UNKNOWN
    
    def _extract_entity(self, text: str, intent: Intent) -> Optional[str]:
        """Extract entity (app name or location) from text dynamically"""
        if intent == Intent.WEATHER:
            # Extract location for weather query
            # Remove weather-related keywords and get the location
            for pattern in ["weather", "temperature", "forecast", "how is the weather", "what's the weather", "current weather"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1:
                        location = parts[1].strip()
                        # Remove common words
                        location = location.replace("in", "").replace("at", "").replace("of", "").replace("the", "")
                        location = location.replace("please", "").replace("can you", "").replace("tell me", "")
                        location = location.strip()
                        if location:
                            return location
            # If no location found, return None (will use default location)
            return None
        
        if intent not in [Intent.OPEN_APP, Intent.CLOSE_APP]:
            return None
        
        # Extract any word after the intent pattern
        for pattern in ["open", "launch", "start", "run", "close", "quit", "exit", "kill"]:
            if pattern in text:
                # Get everything after the pattern
                parts = text.split(pattern)
                if len(parts) > 1:
                    entity = parts[1].strip()
                    # Remove common words and clean up
                    entity = entity.replace("the", "").replace("please", "").replace("can you", "")
                    entity = entity.replace("a", "").replace("an", "").replace("and", "")
                    entity = entity.strip()
                    if entity:
                        return entity
                    
        return None
    
    def get_supported_apps(self) -> List[str]:
        """Get list of supported app names (dynamic - returns empty)"""
        return []
