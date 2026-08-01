"""
Weather Controller
Fetches weather information including temperature, air quality, and pollution data
"""

import requests
from typing import Optional, Dict


class WeatherController:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather controller
        
        Args:
            api_key: OpenWeatherMap API key (optional, will use wttr.in if not provided)
        """
        # Force use of wttr.in (free, no API key required) for reliability
        print("Using wttr.in (free weather service) - no API key required")
        self.api_key = None
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_weather(self, location: Optional[str] = None) -> Optional[Dict]:
        """
        Get weather information for a location
        
        Args:
            location: City name or location (uses default if None)
            
        Returns:
            Dictionary with weather details or None if failed
        """
        if self.api_key:
            return self._get_openweathermap_weather(location)
        else:
            return self._get_wttr_weather(location)
    
    def _get_wttr_weather(self, location: Optional[str] = None) -> Optional[Dict]:
        """
        Get weather from wttr.in (free, no API key required)
        
        Args:
            location: City name or location
            
        Returns:
            Dictionary with weather details
        """
        try:
            # Use wttr.in JSON endpoint
            url = f"https://wttr.in/{location if location else ''}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"✗ Weather API error: {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract current weather
            current = data.get('current_condition', [{}])[0]
            
            # Extract weather description
            weather_desc = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
            
            # Extract temperature
            temp_c = current.get('temp_C', 'N/A')
            temp_f = current.get('temp_F', 'N/A')
            
            # Extract wind
            wind_speed = current.get('windspeedKmph', 'N/A')
            wind_dir = current.get('winddir16Point', 'N/A')
            
            # Extract humidity
            humidity = current.get('humidity', 'N/A')
            
            # Extract feels like
            feels_like_c = current.get('FeelsLikeC', 'N/A')
            
            # Extract UV index
            uv_index = current.get('uvIndex', 'N/A')
            
            # Extract visibility
            visibility = current.get('visibility', 'N/A')
            
            # Extract air quality (if available)
            air_quality = self._get_air_quality(location)
            
            # Format weather info
            weather_info = {
                'location': location if location else 'Current location',
                'temperature_c': temp_c,
                'temperature_f': temp_f,
                'feels_like_c': feels_like_c,
                'weather': weather_desc,
                'wind_speed': wind_speed,
                'wind_direction': wind_dir,
                'humidity': humidity,
                'uv_index': uv_index,
                'visibility': visibility,
                'air_quality': air_quality,
                'pollution': air_quality.get('aqi', 'N/A') if air_quality else 'N/A'
            }
            
            return weather_info
            
        except Exception as e:
            print(f"✗ Error fetching weather: {e}")
            return None
    
    def _get_air_quality(self, location: Optional[str] = None) -> Optional[Dict]:
        """
        Get air quality information
        
        Args:
            location: City name or location
            
        Returns:
            Dictionary with air quality data
        """
        try:
            # Use WAQI API (free)
            url = f"https://api.waqi.info/feed/{location if location else 'here'}/?token=demo"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data.get('status') != 'ok':
                return None
            
            iaqi = data.get('data', {}).get('iaqi', {})
            
            # Extract AQI components
            air_quality = {
                'aqi': data.get('data', {}).get('aqi', 'N/A'),
                'pm25': iaqi.get('pm25', {}).get('v', 'N/A'),
                'pm10': iaqi.get('pm10', {}).get('v', 'N/A'),
                'o3': iaqi.get('o3', {}).get('v', 'N/A'),
                'no2': iaqi.get('no2', {}).get('v', 'N/A'),
                'so2': iaqi.get('so2', {}).get('v', 'N/A'),
                'co': iaqi.get('co', {}).get('v', 'N/A')
            }
            
            return air_quality
            
        except Exception as e:
            print(f"✗Error fetching air quality: {e}")
            return None
    
    def _get_openweathermap_weather(self, location: Optional[str] = None) -> Optional[Dict]:
        """
        Get weather from OpenWeatherMap (requires API key)
        
        Args:
            location: City name or location
            
        Returns:
            Dictionary with weather details
        """
        try:
            # Use current weather endpoint
            url = f"{self.base_url}/weather?q={location if location else 'auto:ip'}&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"✗ Weather API error: {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract weather details
            weather_info = {
                'location': data.get('name', 'Unknown'),
                'temperature_c': data.get('main', {}).get('temp', 'N/A'),
                'feels_like_c': data.get('main', {}).get('feels_like', 'N/A'),
                'weather': data.get('weather', [{}])[0].get('description', 'Unknown'),
                'wind_speed': data.get('wind', {}).get('speed', 'N/A'),
                'wind_direction': data.get('wind', {}).get('deg', 'N/A'),
                'humidity': data.get('main', {}).get('humidity', 'N/A'),
                'visibility': data.get('visibility', 'N/A'),
                'air_quality': None,
                'pollution': 'N/A'
            }
            
            return weather_info
            
        except Exception as e:
            print(f"✗ Error fetching weather: {e}")
            return None
    
    def format_weather_response(self, weather_info: Dict) -> str:
        """
        Format weather information for TTS response
        
        Args:
            weather_info: Weather information dictionary
            
        Returns:
            Formatted string for speech
        """
        if not weather_info:
            return "Sorry, I could not fetch the weather information."
        
        location = weather_info.get('location', 'Unknown')
        temp_c = weather_info.get('temperature_c', 'N/A')
        feels_like = weather_info.get('feels_like_c', 'N/A')
        weather = weather_info.get('weather', 'Unknown')
        wind_speed = weather_info.get('wind_speed', 'N/A')
        wind_dir = weather_info.get('wind_direction', 'N/A')
        humidity = weather_info.get('humidity', 'N/A')
        uv_index = weather_info.get('uv_index', 'N/A')
        pollution = weather_info.get('pollution', 'N/A')
        
        response = f"Sir, the current weather in {location} is {weather}. "
        response += f"The temperature is {temp_c} degrees Celsius, "
        
        if feels_like != 'N/A':
            response += f"but it feels like {feels_like} degrees. "
        
        response += f"The wind is blowing at {wind_speed} kilometers per hour from the {wind_dir} direction. "
        response += f"The humidity level is {humidity} percent. "
        
        if uv_index != 'N/A':
            response += f"The UV index is {uv_index}. "
        
        if pollution != 'N/A':
            response += f"The air quality index is {pollution}. "
        
        # Add pollution status
        if pollution != 'N/A':
            try:
                aqi = int(pollution)
                if aqi <= 50:
                    response += "The air quality is good and safe. "
                elif aqi <= 100:
                    response += "The air quality is moderate. "
                elif aqi <= 150:
                    response += "The air quality is unhealthy for sensitive groups. "
                elif aqi <= 200:
                    response += "The air quality is unhealthy. "
                else:
                    response += "The air quality is very unhealthy. "
            except:
                pass
        
        response += "That's all the weather information I have for you, sir."
        
        return response
