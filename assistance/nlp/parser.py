"""
Command Parser
Parses voice commands and extracts intents and entities
"""

from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass
from assistance.utils.logger import logger


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
    SPOTIFY_PLAY = "spotify_play"
    SPOTIFY_ADD_TO_PLAYLIST = "spotify_add_to_playlist"
    SPOTIFY_CREATE_PLAYLIST = "spotify_create_playlist"
    SPOTIFY_NEXT = "spotify_next"
    SPOTIFY_PREVIOUS = "spotify_previous"
    SPOTIFY_PAUSE = "spotify_pause"
    SPOTIFY_RESUME = "spotify_resume"
    INTERRUPT = "interrupt"
    GREETING = "greeting"
    TERMINAL_EXEC = "terminal_exec"
    PHONE_LOCATION = "phone_location"
    START_TRACKING = "start_tracking"
    STOP_TRACKING = "stop_tracking"
    TRACKING_STATUS = "tracking_status"
    # Messaging intents
    WHATSAPP_READ = "whatsapp_read"
    WHATSAPP_SEND = "whatsapp_send"
    WHATSAPP_UNREAD_COUNT = "whatsapp_unread_count"
    INSTAGRAM_READ = "instagram_read"
    INSTAGRAM_SEND = "instagram_send"
    INSTAGRAM_UNREAD_COUNT = "instagram_unread_count"
    MESSAGES_CHECK = "messages_check"
    MESSAGES_UNREAD_COUNT = "messages_unread_count"
    REPLY_MESSAGE = "reply_message"
    MARK_MESSAGES_READ = "mark_messages_read"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Parsed command result"""
    intent: Intent
    entity: Optional[str] = None
    playlist_entity: Optional[str] = None
    confidence: float = 1.0


class CommandParser:
    def __init__(self):
        """Initialize command parser with PyTorch Neural Engine support"""
        try:
            from assistance.nlp.neural_engine import JeanMaxNeuralEngine
            self.neural_engine = JeanMaxNeuralEngine()
        except Exception as e:
            logger.warning(f"Neural Engine init skipped: {e}", module="Parser")
            self.neural_engine = None

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
            Intent.GREETING: ["hello", "hi", "hey", "who are you", "what is your name", "what's your name", "who made you", "introduce yourself"],
            Intent.PHONE_LOCATION: [
                "where is my phone", "phone location", "find my phone", "locate my phone", 
                "phone kidhar hai", "mera phone kidhar hai", "phone kahan hai", "phone location batao",
                "current phone location", "phone ka location", "phone track karo", "phone location check karo"
            ],
            Intent.START_TRACKING: [
                "start tracking", "start phone tracking", "enable tracking", "activate tracking",
                "phone tracking start karo", "tracking shuru karo", "track my phone", 
                "phone ko track karo", "location tracking start", "monitor my phone",
                "phone lost", "mera phone gayab hai", "phone kho gaya", "find my phone continuously"
            ],
            Intent.STOP_TRACKING: [
                "stop tracking", "stop phone tracking", "disable tracking", "deactivate tracking",
                "phone tracking stop karo", "tracking band karo", "stop monitoring",
                "phone tracking ruk jao", "location tracking stop"
            ],
            Intent.TRACKING_STATUS: [
                "tracking status", "phone tracking status", "tracking information",
                "tracking kaisa chal raha hai", "tracking status batao", "monitoring status"
            ],
            # Messaging intent patterns
            Intent.WHATSAPP_READ: [
                "read my whatsapp messages", "read whatsapp", "check whatsapp messages",
                "whatsapp messages suna", "whatsapp check karo", "show whatsapp messages",
                "whatsapp messages padh", "mera whatsapp check karo"
            ],
            Intent.WHATSAPP_SEND: [
                "send whatsapp message", "whatsapp message bhej", "send message on whatsapp",
                "whatsapp pe message bhejo", "text on whatsapp", "whatsapp kar"
            ],
            Intent.WHATSAPP_UNREAD_COUNT: [
                "how many whatsapp messages", "whatsapp unread count", "unread whatsapp",
                "kitne whatsapp messages", "whatsapp messages kitne hain"
            ],
            Intent.INSTAGRAM_READ: [
                "read my instagram messages", "read instagram", "check instagram messages",
                "instagram messages suna", "instagram check karo", "show instagram messages",
                "instagram dm check", "instagram dms padh"
            ],
            Intent.INSTAGRAM_SEND: [
                "send instagram message", "instagram message bhej", "send message on instagram",
                "instagram pe message bhejo", "dm on instagram", "instagram dm karo"
            ],
            Intent.INSTAGRAM_UNREAD_COUNT: [
                "how many instagram messages", "instagram unread count", "unread instagram",
                "kitne instagram messages", "instagram dms kitne hain"
            ],
            Intent.MESSAGES_CHECK: [
                "check my messages", "read my messages", "check messages",
                "messages check karo", "messages suna", "show messages",
                "mera messages check karo", "kya messages hain"
            ],
            Intent.MESSAGES_UNREAD_COUNT: [
                "how many messages", "unread messages count", "total unread messages",
                "kitne messages hain", "messages kitne unread hain", "message count"
            ],
            Intent.REPLY_MESSAGE: [
                "reply to", "reply karo", "jawab do", "send reply",
                "reply bhej", "respond to"
            ],
            Intent.MARK_MESSAGES_READ: [
                "mark all as read", "mark messages as read", "messages read kar",
                "sab messages read kar do", "mark as read"
            ]
        }
        
    def parse(self, text: str) -> ParsedCommand:
        """
        Parse voice command text using PyTorch Neural Engine when available
        """
        if not text:
            return ParsedCommand(intent=Intent.UNKNOWN)
            
        text_lower = text.lower().strip()
        import re
        
        # Check interruption first
        for keyword in self.intent_patterns[Intent.INTERRUPT]:
            if keyword in text_lower:
                return ParsedCommand(intent=Intent.INTERRUPT)

        # Try Neural Model Prediction first (JeanMax.pt)
        if self.neural_engine and self.neural_engine.is_loaded:
            neural_res = self.neural_engine.predict(text_lower)
            if neural_res and neural_res.intent != Intent.UNKNOWN and neural_res.confidence >= 0.40:
                logger.ai(f"Matched Intent: {neural_res.intent.name} (Conf: {neural_res.confidence*100:.1f}%)", module="NeuralEngine")
                return neural_res

        # Check Spotify Add to Playlist
        if "add" in text_lower and ("playlist" in text_lower or " to " in text_lower or "to my" in text_lower):
            match = re.search(r"add\s+(?:song\s+|track\s+)?(.+?)\s+to\s+(?:my\s+|the\s+)?(?:playlist\s+)?(.+?)(?:\s+playlist)?$", text_lower)
            if match:
                song = match.group(1).strip()
                playlist = match.group(2).strip()
                song = re.sub(r'^(the|a|an)\s+', '', song)
                playlist = re.sub(r'^(the|a|an)\s+', '', playlist)
                if song and playlist:
                    return ParsedCommand(intent=Intent.SPOTIFY_ADD_TO_PLAYLIST, entity=song, playlist_entity=playlist)

        # Check Spotify Create Playlist
        if ("create" in text_lower or "make" in text_lower or "new" in text_lower) and "playlist" in text_lower:
            match = re.search(r"(?:create|make|build|add)\s+(?:a\s+)?(?:new\s+)?playlist\s+(?:called\s+|named\s+)?(.+)", text_lower)
            if match:
                playlist_name = match.group(1).strip()
                playlist_name = re.sub(r'^(the|a|an)\s+', '', playlist_name)
                if playlist_name:
                    return ParsedCommand(intent=Intent.SPOTIFY_CREATE_PLAYLIST, entity=playlist_name)

        # Check Spotify Next / Previous / Pause / Resume
        for kw in ["next track", "next song", "skip song", "skip track", "play next song", "next music"]:
            if kw in text_lower:
                return ParsedCommand(intent=Intent.SPOTIFY_NEXT)

        for kw in ["previous track", "previous song", "last song", "play previous song", "previous music"]:
            if kw in text_lower:
                return ParsedCommand(intent=Intent.SPOTIFY_PREVIOUS)

        for kw in ["pause spotify", "pause music", "pause song", "stop music", "pause playback"]:
            if kw in text_lower:
                return ParsedCommand(intent=Intent.SPOTIFY_PAUSE)

        for kw in ["resume spotify", "resume music", "resume song", "play spotify", "resume playback"]:
            if kw in text_lower:
                return ParsedCommand(intent=Intent.SPOTIFY_RESUME)

        # Check Spotify Play song
        if text_lower.startswith("play ") or "on spotify" in text_lower or text_lower.startswith("spotify play"):
            if text_lower.strip() not in ["play spotify"]:
                match = re.search(r"(?:spotify\s+play\s+|play\s+)(?:song\s+|track\s+)?(.+?)(?:\s+on\s+spotify)?$", text_lower)
                if match:
                    song_name = match.group(1).strip()
                    song_name = re.sub(r'^(the|a|an)\s+', '', song_name)
                    if song_name and song_name not in ["spotify", "music", "song"]:
                        return ParsedCommand(intent=Intent.SPOTIFY_PLAY, entity=song_name)

        # Detect intent using standard pattern dictionary
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

