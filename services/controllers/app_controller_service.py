"""
App Controller Service Implementation
Implements IAppController interface using existing AppManager
"""

from core.interfaces.controller_service import IAppController
from assistance.controllers.app_manager import AppManager


class AppControllerService(IAppController):
    """Application controller service implementation"""
    
    def __init__(self):
        self.app_manager = AppManager()
    
    def open_app(self, app_name: str) -> bool:
        """Open application by name"""
        return self.app_manager.open_app(app_name)
    
    def close_app(self, app_name: str) -> bool:
        """Close application by name"""
        return self.app_manager.close_app(app_name)
    
    def close_all_apps(self) -> bool:
        """Close all applications"""
        return self.app_manager.close_all_apps()
