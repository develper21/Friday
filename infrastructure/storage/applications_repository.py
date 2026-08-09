"""
Applications Repository
Stores and retrieves application data
"""

from core.interfaces.repository import IApplicationsRepository
from .json_repository import JSONRepository


class ApplicationsRepository(JSONRepository):
    """Repository for application data"""
    
    def __init__(self, file_path: str = "data/applications.json"):
        super().__init__(file_path)
    
    async def find_by_name(self, name: str) -> Optional[dict]:
        """Find application by name"""
        all_apps = await self.get_all()
        for app in all_apps:
            if app.get('name', '').lower() == name.lower():
                return app
        return None
