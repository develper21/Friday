"""
Repository Pattern Interfaces
Defines abstract interfaces for data access layer
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class IRepository(ABC):
    """Base repository interface"""
    
    @abstractmethod
    async def get(self, id: str) -> Optional[Dict]:
        """Get item by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Dict]:
        """Get all items"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict) -> Dict:
        """Create new item"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict) -> Dict:
        """Update existing item"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete item by ID"""
        pass


class IApplicationsRepository(IRepository):
    """Repository for application data"""
    pass


class ICommandHistoryRepository(IRepository):
    """Repository for command history"""
    pass


class ILocationHistoryRepository(IRepository):
    """Repository for phone location history"""
    pass
