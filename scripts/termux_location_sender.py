#!/usr/bin/env python3
"""
Termux Location Sender for Jean Max Phone Tracking
This script runs on Android Termux to send GPS location data to Jean Max HTTP server.

Requirements:
- Termux app (from F-Droid recommended)
- Python: pkg install python
- Required packages: pip install requests

Usage:
1. Configure the SERVER_URL and other settings below
2. Grant location permissions: termux-location permission
3. Run script: python termux_location_sender.py
4. For background execution: termux-location sender.py &
"""

import json
import time
import logging
import requests
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime
import signal
import sys


# ==================== CONFIGURATION ====================

# Jean Max HTTP Server URL
# Replace with your laptop's IP address and configured port
SERVER_URL = "http://YOUR_LAPTOP_IP:8080/location"

# Location update interval in seconds
UPDATE_INTERVAL = 30

# Enable GPS accuracy filtering (ignore locations with accuracy > threshold meters)
ACCURACY_THRESHOLD = 100  # meters

# Enable retry on failure
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Enable logging
LOG_FILE = "location_sender.log"

# ==================== LOGGING SETUP ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ==================== LOCATION FETCHING ====================

def get_location_from_termux() -> Optional[Dict[str, Any]]:
    """
    Get location using Termux location API
    Returns location dict with latitude, longitude, accuracy, etc.
    """
    try:
        # Use termux-location command to get GPS data
        result = subprocess.run(
            ['termux-location'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            location_data = json.loads(result.stdout)
            
            # Extract relevant fields
            location = {
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'altitude': location_data.get('altitude'),
                'accuracy': location_data.get('accuracy'),
                'speed': location_data.get('speed'),
                'bearing': location_data.get('bearing'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Validate required fields
            if location['latitude'] is None or location['longitude'] is None:
                logger.error("Invalid location data: missing coordinates")
                return None
            
            logger.info(f"Location obtained: {location['latitude']:.6f}, {location['longitude']:.6f}")
            return location
        else:
            logger.error(f"Termux location failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("Location request timed out")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse location data: {e}")
        return None
    except FileNotFoundError:
        logger.error("termux-location command not found. Install: pkg install termux-api")
        return None
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        return None


def get_location_from_android() -> Optional[Dict[str, Any]]:
    """
    Alternative method using Android location services directly
    This requires additional setup but may be more accurate
    """
    try:
        # This is a placeholder for alternative location methods
        # You could use:
        # - Android location API via plyer library
        # - GPS via serial port
        # - Network-based location
        
        logger.warning("Alternative location method not implemented, using termux-location")
        return get_location_from_termux()
        
    except Exception as e:
        logger.error(f"Error in alternative location method: {e}")
        return None


# ==================== HTTP SENDING ====================

def send_location_to_server(location: Dict[str, Any], server_url: str) -> bool:
    """
    Send location data to Jean Max HTTP server
    
    Args:
        location: Location data dictionary
        server_url: Jean Max server URL
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(
            server_url,
            json=location,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Location sent successfully: {response.json()}")
            return True
        else:
            logger.error(f"Server returned error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("Connection error - check if Jean Max server is running")
        return False
    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return False
    except Exception as e:
        logger.error(f"Error sending location: {e}")
        return False


def send_location_with_retry(location: Dict[str, Any], server_url: str) -> bool:
    """
    Send location with retry logic
    """
    for attempt in range(MAX_RETRIES):
        if send_location_to_server(location, server_url):
            return True
        
        if attempt < MAX_RETRIES - 1:
            logger.info(f"Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    
    logger.error("Failed to send location after all retries")
    return False


# ==================== VALIDATION ====================

def validate_location(location: Dict[str, Any]) -> bool:
    """
    Validate location data before sending
    
    Args:
        location: Location data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    if location.get('latitude') is None or location.get('longitude') is None:
        logger.error("Missing required coordinates")
        return False
    
    # Validate coordinate ranges
    lat = location['latitude']
    lon = location['longitude']
    
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        logger.error(f"Invalid coordinates: {lat}, {lon}")
        return False
    
    # Check accuracy if available
    if location.get('accuracy') and location['accuracy'] > ACCURACY_THRESHOLD:
        logger.warning(f"Location accuracy too low: {location['accuracy']}m")
        # You might want to return False here to filter inaccurate locations
    
    return True


# ==================== MAIN LOOP ====================

class LocationSender:
    """Main location sender class"""
    
    def __init__(self, server_url: str, interval: int = 30):
        self.server_url = server_url
        self.interval = interval
        self.running = False
        self.last_location = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received, stopping...")
        self.running = False
    
    def start(self):
        """Start the location sending loop"""
        logger.info(f"Starting location sender to {self.server_url}")
        logger.info(f"Update interval: {self.interval} seconds")
        self.running = True
        
        while self.running:
            try:
                # Get location
                location = get_location_from_termux()
                
                if location and validate_location(location):
                    # Check if location changed significantly
                    if self._location_changed(location):
                        # Send to server
                        success = send_location_with_retry(location, self.server_url)
                        
                        if success:
                            self.last_location = location
                        else:
                            logger.warning("Failed to send location, will retry next interval")
                    else:
                        logger.info("Location hasn't changed significantly, skipping update")
                else:
                    logger.warning("Invalid or no location data obtained")
                
                # Wait for next interval
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(self.interval)
        
        logger.info("Location sender stopped")
    
    def _location_changed(self, new_location: Dict[str, Any]) -> bool:
        """
        Check if location changed significantly
        Returns True if first location or significant change detected
        """
        if self.last_location is None:
            return True  # First location
        
        # Simple distance calculation using Haversine formula
        lat1 = self.last_location['latitude']
        lon1 = self.last_location['longitude']
        lat2 = new_location['latitude']
        lon2 = new_location['longitude']
        
        # If coordinates are identical, no change
        if lat1 == lat2 and lon1 == lon2:
            return False
        
        # Calculate approximate distance (simplified)
        # For more accuracy, use proper Haversine formula
        distance = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111000  # Rough conversion to meters
        
        # Consider changed if moved more than 10 meters
        return distance > 10


# ==================== ENTRY POINT ====================

def main():
    """Main entry point"""
    # Check if termux-location is available
    try:
        subprocess.run(['termux-location', '--help'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("termux-location not found. Install with: pkg install termux-api")
        logger.error("Then grant location permission: termux-location permission")
        sys.exit(1)
    
    # Check if server URL is configured
    if "YOUR_LAPTOP_IP" in SERVER_URL:
        logger.error("Please configure SERVER_URL with your laptop's IP address")
        logger.error("Edit this script and replace YOUR_LAPTOP_IP with actual IP")
        sys.exit(1)
    
    # Create and start location sender
    sender = LocationSender(SERVER_URL, UPDATE_INTERVAL)
    
    try:
        sender.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
