"""
Weather Plugin Example
Demonstrates how to create a plugin for JeanMax
"""

from core.plugins.plugin_interface import IPlugin
from typing import Dict, Any, Optional


class WeatherPlugin(IPlugin):
    """Weather information plugin"""
    
    @property
    def name(self) -> str:
        return "weather"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides weather information for any location"
    
    def initialize(self, config: Dict[str, Any]):
        """Initialize plugin with configuration"""
        self.api_key = config.get('api_key', None)
        print(f"Weather plugin initialized")
    
    def execute(self, command: str, params: Dict[str, Any]) -> Optional[Any]:
        """Execute plugin command"""
        if command == "get_weather":
            location = params.get('location', 'current')
            return self._get_weather(location)
        elif command == "forecast":
            location = params.get('location', 'current')
            days = params.get('days', 3)
            return self._get_forecast(location, days)
        return None
    
    def _get_weather(self, location: str) -> str:
        """Get current weather for location"""
        # This would integrate with a real weather API
        return f"Weather for {location}: 25°C, Partly cloudy"
    
    def _get_forecast(self, location: str, days: int) -> str:
        """Get weather forecast for location"""
        return f"{days}-day forecast for {location}: Mild temperatures expected"
    
    def shutdown(self):
        """Shutdown plugin and cleanup resources"""
        print("Weather plugin shutdown")
