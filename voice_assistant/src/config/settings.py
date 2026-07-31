"""
Configuration Loader
Loads and manages application configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Audio configuration"""
    device: Optional[str] = None
    sample_rate: int = 16000
    vad_enabled: bool = True
    vad_aggressiveness: int = 2
    frame_duration_ms: int = 30


@dataclass
class SpeechConfig:
    """Speech recognition configuration"""
    model_size: str = "base"
    device: str = "cuda"
    compute_type: str = "int8"
    language: str = "en"


@dataclass
class Config:
    """Main configuration"""
    audio: AudioConfig
    speech: SpeechConfig
    shutdown_delay: int = 10


class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader
        
        Args:
            config_path: Path to config file (default: ~/.config/voice_assistant/config.json)
        """
        if config_path is None:
            config_path = self._default_config_path()
            
        self.config_path = Path(config_path).expanduser()
        
    def _default_config_path(self) -> str:
        """Get default config path"""
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return str(Path(xdg) / "voice_assistant" / "config.json")
        return str(Path.home() / ".config" / "voice_assistant" / "config.json")
    
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
            "shutdown_delay": 10
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_data, f, indent=2)
            
        print(f"Created config at {self.config_path}")
