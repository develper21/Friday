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
    BATTERY = "battery"
    SYSTEM_STATUS = "system_status"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    VOLUME_MUTE = "volume_mute"
    TIME_DATE = "time_date"
    SEARCH_WEB = "search_web"
    INTERRUPT = "interrupt"
    GREETING = "greeting"
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
        self.intent_patterns = {
            Intent.INTERRUPT: [
                "wait jean", "stop jean", "jean wait", "jean stop", 
                "wait please", "wait max", "stop max", "wait a minute", "hold on"
            ],
            Intent.CLOSE_ALL_APPS: ["close all app", "close all application", "quit all apps", "close all apps"],
            Intent.CLOSE_ALL_TABS: ["close all tab", "close all browser", "close tab", "close tabs"],
            Intent.OPEN_APP: ["open", "launch", "start", "run", "search for app"],
            Intent.CLOSE_APP: ["close", "quit", "exit", "kill", "terminate"],
            Intent.POWER_OFF: ["shut down", "power off", "turn off", "shutdown"],
            Intent.RESTART: ["restart", "reboot", "restart system"],
            Intent.WEATHER: ["weather", "temperature", "forecast", "how is the weather", "what's the weather", "current weather", "mausam"],
            Intent.BATTERY: ["battery", "battery percentage", "battery status", "charge", "how much battery"],
            Intent.SYSTEM_STATUS: ["system status", "cpu usage", "ram usage", "memory usage", "system info"],
            Intent.VOLUME_UP: ["volume up", "increase volume", "louder"],
            Intent.VOLUME_DOWN: ["volume down", "decrease volume", "lower volume", "quieter"],
            Intent.VOLUME_MUTE: ["mute volume", "mute audio", "unmute", "mute"],
            Intent.TIME_DATE: ["what time is it", "current time", "what's the time", "time", "date", "today's date", "what is the date"],
            Intent.SEARCH_WEB: ["search google for", "search youtube for", "search web for", "google search", "youtube search", "search for"],
            Intent.GREETING: ["hello", "hi", "hey", "who are you", "what is your name", "what's your name", "who made you", "introduce yourself"]
        }
        
    def parse(self, text: str) -> ParsedCommand:
        """
        Parse voice command text
        """
        if not text:
            return ParsedCommand(intent=Intent.UNKNOWN)
            
        text_lower = text.lower().strip()
        
        # Check interruption first
        for keyword in self.intent_patterns[Intent.INTERRUPT]:
            if keyword in text_lower:
                return ParsedCommand(intent=Intent.INTERRUPT)

        # Detect intent
        intent = self._detect_intent(text_lower)
        
        # Extract entity
        entity = self._extract_entity(text_lower, intent)
        
        return ParsedCommand(intent=intent, entity=entity)
    
    def _detect_intent(self, text: str) -> Intent:
        """Detect intent from text"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return intent
        return Intent.UNKNOWN
    
    def _extract_entity(self, text: str, intent: Intent) -> Optional[str]:
        """Extract entity (app name, location, or search query)"""
        if intent == Intent.WEATHER:
            for pattern in ["weather", "temperature", "forecast", "how is the weather", "what's the weather", "current weather", "mausam"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1:
                        loc = parts[1].strip()
                        loc = loc.replace("in", "").replace("at", "").replace("of", "").replace("the", "")
                        loc = loc.replace("please", "").replace("can you", "").replace("tell me", "").strip()
                        if loc:
                            return loc
                    if len(parts) > 0:
                        loc = parts[0].strip()
                        loc = loc.replace("in", "").replace("at", "").replace("of", "").replace("the", "")
                        loc = loc.replace("please", "").replace("can you", "").replace("tell me", "").replace("for", "").strip()
                        if loc:
                            return loc
            return None

        if intent == Intent.SEARCH_WEB:
            for pattern in ["search google for", "search youtube for", "search web for", "google search", "youtube search", "search for"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
            return text
        
        if intent in [Intent.OPEN_APP, Intent.CLOSE_APP]:
            for pattern in ["open", "launch", "start", "run", "close", "quit", "exit", "kill", "terminate"]:
                if pattern in text:
                    parts = text.split(pattern)
                    if len(parts) > 1:
                        entity = parts[1].strip()
                        entity = entity.replace("the", "").replace("please", "").replace("can you", "")
                        entity = entity.replace("app", "").replace("application", "").replace("a", "").replace("an", "").strip()
                        if entity:
                            return entity
                    
        return None

