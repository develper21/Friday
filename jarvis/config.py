"""
Configuration compatibility module.
"""

from assistance.config.settings import ConfigLoader, Config, AudioConfig, SpeechConfig, WeatherConfig
from pathlib import Path
import os

def default_config_path():
    """Get default config path"""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "voice_assistant" / "config.json"
    return Path.home() / ".config" / "voice_assistant" / "config.json"

def _default_db_path():
    """Get default database path"""
    return Path.home() / ".local" / "share" / "voice_assistant" / "database.db"

def load_config():
    """Load configuration"""
    loader = ConfigLoader()
    return loader.load()

def load_settings():
    """Load settings (alias for load_config)"""
    return load_config()

def get_default_config():
    """Get default configuration"""
    return Config(
        audio=AudioConfig(),
        speech=SpeechConfig(),
        weather=WeatherConfig()
    )

def _load_json(path):
    """Load JSON file"""
    import json
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None

def _save_json(path, data):
    """Save JSON file"""
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

SUPPORTED_CHAT_MODELS = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"

def get_supported_model_ids():
    """Get supported model IDs"""
    return SUPPORTED_CHAT_MODELS

__all__ = [
    'default_config_path', '_default_db_path', 'load_config', 'load_settings',
    'get_default_config', '_load_json', '_save_json', 'SUPPORTED_CHAT_MODELS',
    'DEFAULT_CHAT_MODEL', 'get_supported_model_ids'
]
