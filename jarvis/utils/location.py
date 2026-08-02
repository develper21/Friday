"""
Location utilities compatibility module.
Provides stub implementations for desktop app compatibility.
"""

from pathlib import Path
from typing import Optional, Dict, Any

def get_location_info() -> Dict[str, Any]:
    """Get location information."""
    return {"city": "Unknown", "country": "Unknown", "latitude": None, "longitude": None}

def get_location_context() -> str:
    """Get location context string."""
    return "Unknown location"

def is_location_available() -> bool:
    """Check if location services are available."""
    return False

def _get_database_path() -> Path:
    """Get database path."""
    from jarvis.config import _default_db_path
    return _default_db_path()

def _is_private_ip(ip: str) -> bool:
    """Check if IP is private."""
    try:
        import ipaddress
        return ipaddress.ip_address(ip).is_private
    except Exception:
        return False

def _is_cgnat_ip(ip: str) -> bool:
    """Check if IP is CGNAT."""
    try:
        import ipaddress
        addr = ipaddress.ip_address(ip)
        return addr.is_private and (addr.startswith('100.64.') or addr.startswith('192.0.0.'))
    except Exception:
        return False
