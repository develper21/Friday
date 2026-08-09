"""
Weather Controller Service Implementation
Implements IWeatherController interface using existing WeatherController
"""

from typing import Optional
from core.interfaces.controller_service import IWeatherController
from assistance.controllers.weather_controller import WeatherController


class WeatherControllerService(IWeatherController):
    """Weather controller service implementation"""
    
    def __init__(self, api_key: str = None):
        self.weather_controller = WeatherController(api_key)
    
    def get_weather(self, location: Optional[str] = None) -> Optional[dict]:
        """Get weather information"""
        return self.weather_controller.get_weather(location)
    
    def format_weather_response(self, weather_data: dict) -> str:
        """Format weather data for speech"""
        return self.weather_controller.format_weather_response(weather_data)
