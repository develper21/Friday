"""
Configuration Loader
Loads and manages application configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.security.secrets import SecretManager
    SECRETS_AVAILABLE = True
except ImportError:
    SECRETS_AVAILABLE = False


@dataclass
class AudioConfig:
    """Audio configuration"""
    device: Optional[str] = None
    sample_rate: int = 16000
    vad_enabled: bool = True
    vad_aggressiveness: int = 2
    frame_duration_ms: int = 30
    
    def __post_init__(self):
        """Validate configuration values"""
        valid_sample_rates = [8000, 16000, 44100, 48000]
        if self.sample_rate not in valid_sample_rates:
            raise ValueError(f"Sample rate must be one of {valid_sample_rates}, got {self.sample_rate}")
        
        if not 0 <= self.vad_aggressiveness <= 3:
            raise ValueError(f"VAD aggressiveness must be between 0 and 3, got {self.vad_aggressiveness}")
        
        if not 10 <= self.frame_duration_ms <= 100:
            raise ValueError(f"Frame duration must be between 10 and 100ms, got {self.frame_duration_ms}")


@dataclass
class SpeechConfig:
    """Speech recognition configuration"""
    model_size: str = "base"
    device: str = "cuda"
    compute_type: str = "int8"
    language: str = "en"
    
    def __post_init__(self):
        """Validate configuration values"""
        valid_model_sizes = ["tiny", "base", "small", "medium", "large"]
        if self.model_size not in valid_model_sizes:
            raise ValueError(f"Model size must be one of {valid_model_sizes}, got {self.model_size}")
        
        valid_devices = ["cuda", "cpu", "auto"]
        if self.device not in valid_devices:
            raise ValueError(f"Device must be one of {valid_devices}, got {self.device}")
        
        valid_compute_types = ["int8", "float16", "float32"]
        if self.compute_type not in valid_compute_types:
            raise ValueError(f"Compute type must be one of {valid_compute_types}, got {self.compute_type}")
        
        if not 2 <= len(self.language) <= 10:
            raise ValueError(f"Language code must be 2-10 characters, got {len(self.language)}")


@dataclass
class WeatherConfig:
    """Weather API configuration"""
    api_key: Optional[str] = None


@dataclass
class PhoneTrackingConfig:
    """Phone tracking configuration"""
    enabled: bool = True
    device_id: str = "default"
    http_server_port: int = 8080
    http_server_host: str = "0.0.0.0"
    location_change_threshold: int = 100  # meters
    monitoring_interval: int = 30  # seconds
    alert_cooldown: int = 300  # seconds (5 minutes)
    max_location_history: int = 1000
    enable_location_prediction: bool = False
    auto_start_tracking: bool = False
    default_tracking_mode: str = "passive"  # passive, active, continuous
    
    def __post_init__(self):
        """Validate configuration values"""
        if not 1024 <= self.http_server_port <= 65535:
            raise ValueError(f"HTTP server port must be between 1024 and 65535, got {self.http_server_port}")
        
        if not 10 <= self.location_change_threshold <= 10000:
            raise ValueError(f"Location change threshold must be between 10 and 10000 meters, got {self.location_change_threshold}")
        
        if not 5 <= self.monitoring_interval <= 300:
            raise ValueError(f"Monitoring interval must be between 5 and 300 seconds, got {self.monitoring_interval}")
        
        if not 60 <= self.alert_cooldown <= 3600:
            raise ValueError(f"Alert cooldown must be between 60 and 3600 seconds, got {self.alert_cooldown}")
        
        if not 100 <= self.max_location_history <= 10000:
            raise ValueError(f"Max location history must be between 100 and 10000, got {self.max_location_history}")
        
        valid_modes = ["passive", "active", "continuous"]
        if self.default_tracking_mode not in valid_modes:
            raise ValueError(f"Default tracking mode must be one of {valid_modes}, got {self.default_tracking_mode}")


@dataclass
class Config:
    """Main configuration"""
    audio: AudioConfig
    speech: SpeechConfig
    weather: WeatherConfig
    phone_tracking: PhoneTrackingConfig = field(default_factory=PhoneTrackingConfig)
    shutdown_delay: int = 10
    
    def __post_init__(self):
        """Validate configuration values"""
        if not 0 <= self.shutdown_delay <= 60:
            raise ValueError(f"Shutdown delay must be between 0 and 60 seconds, got {self.shutdown_delay}")


class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader
        
        Args:
            config_path: Path to config file (default: local config.json, then ~/.config/voice_assistant/config.json)
        """
        # Load .env file from project root
        self._load_env()
        
        if config_path is None:
            # Try local config first, then system config
            project_root = Path(__file__).parent.parent.parent
            local_config = project_root / "config" / "config.json"
            if local_config.exists():
                config_path = str(local_config)
                print(f"Using local config: {local_config}")
            else:
                config_path = self._default_config_path()
            
        self.config_path = Path(config_path).expanduser()
        
        # Initialize secret manager if available
        self.secret_manager = None
        if SECRETS_AVAILABLE:
            try:
                self.secret_manager = SecretManager()
                print("Secure secret management enabled")
            except Exception as e:
                print(f"Failed to initialize secret manager: {e}")
    
    def _load_env(self):
        """Load .env file from project root"""
        # Get the project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Loaded environment variables from {env_file}")
    
    def _default_config_path(self) -> str:
        """Get default config path"""
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return str(Path(xdg) / "voice_assistant" / "config.json")
        return str(Path.home() / ".config" / "voice_assistant" / "config.json")
    
    def _get_api_key(self, env_var: str, secret_name: str) -> Optional[str]:
        """
        Get API key from secure storage or environment variable
        
        Args:
            env_var: Environment variable name
            secret_name: Secret name for secure storage
            
        Returns:
            API key or None
        """
        # Try secure storage first
        if self.secret_manager:
            try:
                key = self.secret_manager.get_secret(secret_name)
                if key:
                    return key
            except Exception:
                pass
        
        # Fallback to environment variable
        return os.environ.get(env_var)
    
    def load(self) -> Config:
        """
        Load configuration from file
        
        Returns:
            Config object
        """
        if not self.config_path.exists():
            print(f"Config not found at {self.config_path}")
            print("Creating default config...")
            self._create_default_config()
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                
            return Config(
                audio=AudioConfig(
                    device=data.get('audio', {}).get('device'),
                    sample_rate=data.get('audio', {}).get('sample_rate', 16000),
                    vad_enabled=data.get('audio', {}).get('vad_enabled', True),
                    vad_aggressiveness=data.get('audio', {}).get('vad_aggressiveness', 2),
                    frame_duration_ms=data.get('audio', {}).get('frame_duration_ms', 30)
                ),
                speech=SpeechConfig(
                    model_size=data.get('speech', {}).get('model_size', 'base'),
                    device=data.get('speech', {}).get('device', 'cuda'),
                    compute_type=data.get('speech', {}).get('compute_type', 'int8'),
                    language=data.get('speech', {}).get('language', 'en')
                ),
                weather=WeatherConfig(
                    api_key=self._get_api_key('OPENWEATHERMAP_API_KEY', 'openweathermap_api_key')
                ),
                phone_tracking=PhoneTrackingConfig(
                    enabled=data.get('phone_tracking', {}).get('enabled', True),
                    device_id=data.get('phone_tracking', {}).get('device_id', 'default'),
                    http_server_port=data.get('phone_tracking', {}).get('http_server_port', 8080),
                    http_server_host=data.get('phone_tracking', {}).get('http_server_host', '0.0.0.0'),
                    location_change_threshold=data.get('phone_tracking', {}).get('location_change_threshold', 100),
                    monitoring_interval=data.get('phone_tracking', {}).get('monitoring_interval', 30),
                    alert_cooldown=data.get('phone_tracking', {}).get('alert_cooldown', 300),
                    max_location_history=data.get('phone_tracking', {}).get('max_location_history', 1000),
                    enable_location_prediction=data.get('phone_tracking', {}).get('enable_location_prediction', False),
                    auto_start_tracking=data.get('phone_tracking', {}).get('auto_start_tracking', False),
                    default_tracking_mode=data.get('phone_tracking', {}).get('default_tracking_mode', 'passive')
                ),
                shutdown_delay=data.get('shutdown_delay', 10)
            )
            
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            return self._default_config()
    
    def _default_config(self) -> Config:
        """Get default configuration"""
        return Config(
            audio=AudioConfig(),
            speech=SpeechConfig(),
            weather=WeatherConfig(
                api_key=self._get_api_key('OPENWEATHERMAP_API_KEY', 'openweathermap_api_key')
            ),
            phone_tracking=PhoneTrackingConfig(),
            shutdown_delay=10
        )
    
    def _create_default_config(self):
        """Create default config file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_data = {
            "audio": {
                "device": "USB Audio Device",
                "sample_rate": 16000,
                "vad_enabled": True,
                "vad_aggressiveness": 2,
                "frame_duration_ms": 30
            },
            "speech": {
                "model_size": "base",
                "device": "cuda",
                "compute_type": "int8",
                "language": "en"
            },
            "phone_tracking": {
                "enabled": True,
                "device_id": "default",
                "http_server_port": 8080,
                "http_server_host": "0.0.0.0",
                "location_change_threshold": 100,
                "monitoring_interval": 30,
                "alert_cooldown": 300,
                "max_location_history": 1000,
                "enable_location_prediction": False,
                "auto_start_tracking": False,
                "default_tracking_mode": "passive"
            },
            "shutdown_delay": 10
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_data, f, indent=2)
            
        print(f"Created config at {self.config_path}")
