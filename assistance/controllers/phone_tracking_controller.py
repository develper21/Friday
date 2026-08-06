#!/usr/bin/env python3
"""
Advanced Phone Tracking Controller
Provides comprehensive phone location tracking, monitoring, and alert system
with database persistence, threading, and real-time location change detection.
"""

import json
import sqlite3
import threading
import time
import logging
import math
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib


class TrackingMode(Enum):
    """Phone tracking modes"""
    PASSIVE = "passive"  # Only respond to location queries
    ACTIVE = "active"    # Monitor location changes and alert
    CONTINUOUS = "continuous"  # Track continuously and report updates


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class LocationData:
    """Structured location data"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: Optional[str] = None
    speed: Optional[float] = None
    bearing: Optional[float] = None
    device_id: Optional[str] = None
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationData':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class LocationAlert:
    """Location change alert"""
    severity: AlertSeverity
    message: str
    previous_location: LocationData
    current_location: LocationData
    distance_moved: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'severity': self.severity.value,
            'message': self.message,
            'previous_location': self.previous_location.to_dict(),
            'current_location': self.current_location.to_dict(),
            'distance_moved': self.distance_moved,
            'timestamp': self.timestamp
        }


class PhoneTrackingDatabase:
    """Database manager for phone tracking data"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        if db_path is None:
            # Default to project data directory
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "phone_tracking.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self._lock = threading.Lock()
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Locations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    altitude REAL,
                    accuracy REAL,
                    speed REAL,
                    bearing REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    previous_location_json TEXT NOT NULL,
                    current_location_json TEXT NOT NULL,
                    distance_moved REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tracking sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracking_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    mode TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_locations_device_timestamp 
                ON locations(device_id, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_device_timestamp 
                ON alerts(device_id, timestamp DESC)
            """)
            
            conn.commit()
    
    def store_location(self, location: LocationData, device_id: str = "default") -> bool:
        """Store location data in database"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO locations 
                        (device_id, latitude, longitude, altitude, accuracy, speed, bearing, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        device_id,
                        location.latitude,
                        location.longitude,
                        location.altitude,
                        location.accuracy,
                        location.speed,
                        location.bearing,
                        location.timestamp
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error storing location: {e}")
            return False
    
    def get_latest_location(self, device_id: str = "default") -> Optional[LocationData]:
        """Get the most recent location for a device"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT latitude, longitude, altitude, accuracy, speed, bearing, timestamp
                    FROM locations
                    WHERE device_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (device_id,))
                
                row = cursor.fetchone()
                if row:
                    return LocationData(
                        latitude=row[0],
                        longitude=row[1],
                        altitude=row[2],
                        accuracy=row[3],
                        speed=row[4],
                        bearing=row[5],
                        timestamp=row[6]
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting latest location: {e}")
            return None
    
    def get_location_history(self, device_id: str = "default", 
                           limit: int = 100) -> List[LocationData]:
        """Get location history for a device"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT latitude, longitude, altitude, accuracy, speed, bearing, timestamp
                    FROM locations
                    WHERE device_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (device_id, limit))
                
                locations = []
                for row in cursor.fetchall():
                    locations.append(LocationData(
                        latitude=row[0],
                        longitude=row[1],
                        altitude=row[2],
                        accuracy=row[3],
                        speed=row[4],
                        bearing=row[5],
                        timestamp=row[6]
                    ))
                return locations
        except Exception as e:
            logging.error(f"Error getting location history: {e}")
            return []
    
    def store_alert(self, alert: LocationAlert, device_id: str = "default") -> bool:
        """Store alert in database"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO alerts 
                        (device_id, severity, message, previous_location_json, 
                         current_location_json, distance_moved, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        device_id,
                        alert.severity.value,
                        alert.message,
                        json.dumps(alert.previous_location.to_dict()),
                        json.dumps(alert.current_location.to_dict()),
                        alert.distance_moved,
                        alert.timestamp
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logging.error(f"Error storing alert: {e}")
            return False
    
    def get_recent_alerts(self, device_id: str = "default", 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts for a device"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT severity, message, previous_location_json, 
                           current_location_json, distance_moved, timestamp
                    FROM alerts
                    WHERE device_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (device_id, limit))
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'severity': row[0],
                        'message': row[1],
                        'previous_location': json.loads(row[2]),
                        'current_location': json.loads(row[3]),
                        'distance_moved': row[4],
                        'timestamp': row[5]
                    })
                return alerts
        except Exception as e:
            logging.error(f"Error getting recent alerts: {e}")
            return []
    
    def start_tracking_session(self, device_id: str = "default", 
                               mode: TrackingMode = TrackingMode.ACTIVE) -> int:
        """Start a new tracking session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tracking_sessions (device_id, mode, started_at, status)
                    VALUES (?, ?, ?, 'active')
                """, (device_id, mode.value, datetime.utcnow().isoformat()))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error starting tracking session: {e}")
            return -1
    
    def end_tracking_session(self, session_id: int) -> bool:
        """End a tracking session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tracking_sessions
                    SET ended_at = ?, status = 'completed'
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), session_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error ending tracking session: {e}")
            return False


class LocationCalculator:
    """Advanced location calculations using geospatial algorithms"""
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in meters
        """
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, 
                        lat2: float, lon2: float) -> float:
        """Calculate bearing between two points in degrees"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    @staticmethod
    def calculate_speed(distance_m: float, time_seconds: float) -> float:
        """Calculate speed in m/s"""
        if time_seconds == 0:
            return 0.0
        return distance_m / time_seconds
    
    @staticmethod
    def is_location_significant_change(old_loc: LocationData, 
                                     new_loc: LocationData,
                                     threshold_meters: float = 100) -> bool:
        """Check if location change is significant"""
        distance = LocationCalculator.haversine_distance(
            old_loc.latitude, old_loc.longitude,
            new_loc.latitude, new_loc.longitude
        )
        return distance >= threshold_meters


class PhoneTrackingController:
    """
    Advanced Phone Tracking Controller
    Manages phone location tracking, monitoring, and alert system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize phone tracking controller"""
        self.config = config or self._default_config()
        
        # Initialize database
        self.db = PhoneTrackingDatabase(self.config.get('database_path'))
        
        # Initialize calculator
        self.calculator = LocationCalculator()
        
        # Tracking state
        self.current_mode = TrackingMode.PASSIVE
        self.is_monitoring = False
        self.monitoring_thread = None
        self.device_id = self.config.get('device_id', 'default')
        
        # Location cache
        self._last_location: Optional[LocationData] = None
        self._location_cache_lock = threading.Lock()
        
        # Alert callbacks
        self.alert_callbacks = []
        
        # HTTP server (will be initialized separately)
        self.http_server = None
        self.http_server_port = self.config.get('http_server_port', 8080)
        
        # Setup logging
        self._setup_logging()
        
        logging.info("PhoneTrackingController initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'database_path': None,
            'device_id': 'default',
            'http_server_port': 8080,
            'location_change_threshold': 100,  # meters
            'monitoring_interval': 30,  # seconds
            'alert_cooldown': 300,  # seconds (5 minutes)
            'max_location_history': 1000,
            'enable_location_prediction': False
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def register_alert_callback(self, callback):
        """Register a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def receive_location(self, location_data: Dict[str, Any]) -> bool:
        """
        Receive location data from external source
        This is called when location data is received via HTTP API
        """
        try:
            # Parse location data
            location = LocationData.from_dict(location_data)
            
            # Store in database
            success = self.db.store_location(location, self.device_id)
            
            if success:
                logging.info(f"Location received: {location.latitude}, {location.longitude}")
                
                # Check for location change if in active mode
                if self.current_mode in [TrackingMode.ACTIVE, TrackingMode.CONTINUOUS]:
                    self._check_location_change(location)
                
                # Update cache
                with self._location_cache_lock:
                    self._last_location = location
                
                return True
            
            return False
        except Exception as e:
            logging.error(f"Error receiving location: {e}")
            return False
    
    def _check_location_change(self, new_location: LocationData):
        """Check if location has changed significantly and trigger alerts"""
        with self._location_cache_lock:
            old_location = self._last_location
        
        if old_location is None:
            logging.info("First location received, no previous location to compare")
            return
        
        # Calculate distance
        distance = self.calculator.haversine_distance(
            old_location.latitude, old_location.longitude,
            new_location.latitude, new_location.longitude
        )
        
        threshold = self.config.get('location_change_threshold', 100)
        
        if distance >= threshold:
            # Create alert
            alert = self._create_location_alert(old_location, new_location, distance)
            
            # Store alert
            self.db.store_alert(alert, self.device_id)
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logging.error(f"Error in alert callback: {e}")
            
            logging.warning(f"Location change detected: {distance:.2f} meters")
    
    def _create_location_alert(self, old_loc: LocationData, 
                             new_loc: LocationData, 
                             distance: float) -> LocationAlert:
        """Create a location change alert"""
        # Determine severity based on distance
        if distance > 1000:
            severity = AlertSeverity.CRITICAL
            message = f"Critical: Phone location changed significantly ({distance:.0f}m). Please verify phone location."
        elif distance > 500:
            severity = AlertSeverity.WARNING
            message = f"Warning: Phone location changed ({distance:.0f}m). Please check if phone is with you."
        else:
            severity = AlertSeverity.INFO
            message = f"Info: Phone location changed ({distance:.0f}m)."
        
        return LocationAlert(
            severity=severity,
            message=message,
            previous_location=old_loc,
            current_location=new_loc,
            distance_moved=distance,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def get_current_location(self) -> Optional[LocationData]:
        """Get current phone location"""
        with self._location_cache_lock:
            if self._last_location:
                return self._last_location
        
        # Fallback to database
        return self.db.get_latest_location(self.device_id)
    
    def get_location_summary(self) -> Dict[str, Any]:
        """Get comprehensive location summary"""
        current_location = self.get_current_location()
        location_history = self.db.get_location_history(self.device_id, limit=10)
        recent_alerts = self.db.get_recent_alerts(self.device_id, limit=5)
        
        return {
            'current_location': current_location.to_dict() if current_location else None,
            'location_history_count': len(location_history),
            'recent_locations': [loc.to_dict() for loc in location_history[:3]],
            'recent_alerts_count': len(recent_alerts),
            'tracking_mode': self.current_mode.value,
            'is_monitoring': self.is_monitoring,
            'device_id': self.device_id
        }
    
    def start_tracking(self, mode: TrackingMode = TrackingMode.ACTIVE) -> bool:
        """Start phone tracking with specified mode"""
        try:
            # Update mode
            self.current_mode = mode
            
            # Start tracking session in database
            session_id = self.db.start_tracking_session(self.device_id, mode)
            
            if mode == TrackingMode.CONTINUOUS:
                # Start background monitoring thread
                self._start_monitoring()
            
            logging.info(f"Tracking started in {mode.value} mode (session: {session_id})")
            return True
        except Exception as e:
            logging.error(f"Error starting tracking: {e}")
            return False
    
    def stop_tracking(self) -> bool:
        """Stop phone tracking"""
        try:
            # Stop monitoring if running
            if self.is_monitoring:
                self._stop_monitoring()
            
            # Update mode to passive
            self.current_mode = TrackingMode.PASSIVE
            
            logging.info("Tracking stopped")
            return True
        except Exception as e:
            logging.error(f"Error stopping tracking: {e}")
            return False
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logging.info("Background monitoring started")
    
    def _stop_monitoring(self):
        """Stop background monitoring thread"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            self.monitoring_thread = None
        logging.info("Background monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop for continuous tracking"""
        interval = self.config.get('monitoring_interval', 30)
        
        while self.is_monitoring:
            try:
                # Check for location updates
                current_location = self.get_current_location()
                
                if current_location and self._last_location:
                    # In continuous mode, report location periodically
                    if self.current_mode == TrackingMode.CONTINUOUS:
                        self._report_location_update(current_location)
                
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _report_location_update(self, location: LocationData):
        """Report location update in continuous mode"""
        # This would trigger TTS to report location
        for callback in self.alert_callbacks:
            try:
                # Create a simple info alert for location update
                alert = LocationAlert(
                    severity=AlertSeverity.INFO,
                    message=f"Phone location update: {location.latitude:.4f}, {location.longitude:.4f}",
                    previous_location=location,
                    current_location=location,
                    distance_moved=0,
                    timestamp=datetime.utcnow().isoformat()
                )
                callback(alert)
            except Exception as e:
                logging.error(f"Error in location update callback: {e}")
    
    def format_location_response(self, location: Optional[LocationData]) -> str:
        """Format location data for voice response"""
        if not location:
            return "Sorry sir, I don't have current location data for your phone."
        
        # Get location history for context
        history = self.db.get_location_history(self.device_id, limit=2)
        
        if len(history) > 1:
            prev_loc = history[1]
            distance = self.calculator.haversine_distance(
                prev_loc.latitude, prev_loc.longitude,
                location.latitude, location.longitude
            )
            
            if distance > 100:
                return (f"Sir, your phone is currently at latitude {location.latitude:.4f} "
                       f"and longitude {location.longitude:.4f}. "
                       f"Note: Your phone has moved approximately {distance:.0f} meters "
                       f"from its previous location. Please check if your phone is with you.")
        
        return (f"Sir, your phone is currently at latitude {location.latitude:.4f} "
               f"and longitude {location.longitude:.4f}. "
               f"Location accuracy is {location.accuracy:.0f} meters if available.")
    
    def get_tracking_status(self) -> str:
        """Get current tracking status for voice response"""
        mode_desc = {
            TrackingMode.PASSIVE: "passive mode - only responding to location queries",
            TrackingMode.ACTIVE: "active mode - monitoring location changes",
            TrackingMode.CONTINUOUS: "continuous mode - tracking and reporting location updates"
        }
        
        status = f"Phone tracking is currently in {mode_desc.get(self.current_mode, 'unknown mode')}"
        
        if self.is_monitoring:
            status += " with background monitoring active"
        
        location = self.get_current_location()
        if location:
            status += f". Last known location: {location.latitude:.4f}, {location.longitude:.4f}"
        else:
            status += ". No location data available yet"
        
        return status
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_tracking()
        logging.info("PhoneTrackingController cleaned up")
