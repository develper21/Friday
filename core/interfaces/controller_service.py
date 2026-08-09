"""
Controller Service Interfaces
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IAppController(ABC):
    """Interface for application management"""
    
    @abstractmethod
    def open_app(self, app_name: str) -> bool:
        """Open application by name"""
        pass
    
    @abstractmethod
    def close_app(self, app_name: str) -> bool:
        """Close application by name"""
        pass
    
    @abstractmethod
    def close_all_apps(self) -> bool:
        """Close all applications"""
        pass


class ISystemController(ABC):
    """Interface for system control"""
    
    @abstractmethod
    def get_battery_info(self) -> str:
        """Get battery information"""
        pass
    
    @abstractmethod
    def get_system_status(self) -> str:
        """Get system status"""
        pass
    
    @abstractmethod
    def get_time_date(self) -> str:
        """Get current time and date"""
        pass
    
    @abstractmethod
    def set_volume(self, action: str) -> str:
        """Set system volume"""
        pass
    
    @abstractmethod
    def search_web(self, query: str) -> str:
        """Search web"""
        pass
    
    @abstractmethod
    def power_off(self, delay: int = 0) -> bool:
        """Power off system"""
        pass
    
    @abstractmethod
    def restart(self, delay: int = 0) -> bool:
        """Restart system"""
        pass


class IWeatherController(ABC):
    """Interface for weather information"""
    
    @abstractmethod
    def get_weather(self, location: Optional[str] = None) -> Optional[dict]:
        """Get weather information"""
        pass
    
    @abstractmethod
    def format_weather_response(self, weather_data: dict) -> str:
        """Format weather data for speech"""
        pass


class ISpotifyController(ABC):
    """Interface for Spotify control"""
    
    @abstractmethod
    def play_song(self, song_name: str) -> Tuple[bool, str]:
        """Play song on Spotify"""
        pass
    
    @abstractmethod
    def add_to_playlist(self, song: str, playlist: str) -> Tuple[bool, str]:
        """Add song to playlist"""
        pass
    
    @abstractmethod
    def create_playlist(self, playlist_name: str) -> Tuple[bool, str]:
        """Create new playlist"""
        pass
    
    @abstractmethod
    def change_track(self, action: str) -> Tuple[bool, str]:
        """Change track (next/previous/pause/resume)"""
        pass


class ITerminalController(ABC):
    """Interface for terminal command execution"""
    
    @abstractmethod
    def execute_task_by_phrase(self, phrase: str) -> Tuple[bool, str]:
        """Execute terminal command by natural language phrase"""
        pass
    
    @abstractmethod
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """Execute raw terminal command"""
        pass


class IPhoneTrackingController(ABC):
    """Interface for phone tracking"""
    
    @abstractmethod
    def start_tracking(self, mode) -> bool:
        """Start phone tracking"""
        pass
    
    @abstractmethod
    def stop_tracking(self) -> bool:
        """Stop phone tracking"""
        pass
    
    @abstractmethod
    def get_current_location(self) -> Optional[dict]:
        """Get current phone location"""
        pass
    
    @abstractmethod
    def get_tracking_status(self) -> str:
        """Get tracking status"""
        pass
    
    @abstractmethod
    def register_alert_callback(self, callback):
        """Register callback for alerts"""
        pass
