"""
JSON-based Repository Implementation
Simple file-based storage for development
"""

import json
import os
from typing import List, Optional, Dict
from core.interfaces.repository import IRepository


class JSONRepository(IRepository):
    """Base JSON repository implementation"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure JSON file exists"""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                json.dump({}, f)
    
    def _load_data(self) -> Dict:
        """Load data from JSON file"""
        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self, data: Dict):
        """Save data to JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get item by ID"""
        data = self._load_data()
        return data.get(id)
    
    async def get_all(self) -> List[Dict]:
        """Get all items"""
        data = self._load_data()
        return list(data.values())
    
    async def create(self, data: Dict) -> Dict:
        """Create new item"""
        all_data = self._load_data()
        item_id = data.get('id', str(len(all_data) + 1))
        data['id'] = item_id
        all_data[item_id] = data
        self._save_data(all_data)
        return data
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update existing item"""
        all_data = self._load_data()
        if id in all_data:
            all_data[id].update(data)
            self._save_data(all_data)
            return all_data[id]
        return None
    
    async def delete(self, id: str) -> bool:
        """Delete item by ID"""
        all_data = self._load_data()
        if id in all_data:
            del all_data[id]
            self._save_data(all_data)
            return True
        return False
