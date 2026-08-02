"""
Dictation history compatibility module.
"""

from pathlib import Path
import json
from typing import List, Dict, Any

def _default_history_path() -> Path:
    """Get default history file path."""
    from jarvis.config import _default_db_path
    db_path = _default_db_path()
    return db_path.parent / "dictation_history.json"

class DictationHistory:
    """Dictation history manager"""
    def __init__(self):
        self._history_path = _default_history_path()
        self._entries: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self):
        """Load history from file"""
        if self._history_path.exists():
            try:
                with open(self._history_path, 'r') as f:
                    self._entries = json.load(f)
            except Exception:
                self._entries = []
    
    def add_entry(self, text: str, timestamp: float = None):
        """Add a new dictation entry"""
        import time
        entry = {
            'text': text,
            'timestamp': timestamp or time.time()
        }
        self._entries.append(entry)
        self._save()
    
    def _save(self):
        """Save history to file"""
        try:
            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._history_path, 'w') as f:
                json.dump(self._entries, f, indent=2)
        except Exception:
            pass
    
    def get_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent entries"""
        return self._entries[-limit:]
