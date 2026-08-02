"""
Memory database compatibility module.
"""

from pathlib import Path
import json
from typing import Dict, Any, Optional

class Database:
    """Database compatibility stub"""
    def __init__(self, db_path: Path = None):
        self._db_path = db_path
        self._data: Dict[str, Any] = {}
    
    def load(self):
        """Load database"""
        if self._db_path and self._db_path.exists():
            try:
                with open(self._db_path, 'r') as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
    
    def save(self):
        """Save database"""
        if self._db_path:
            try:
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._db_path, 'w') as f:
                    json.dump(self._data, f, indent=2)
            except Exception:
                pass
    
    def get(self, key: str, default=None) -> Any:
        """Get value from database"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value in database"""
        self._data[key] = value
