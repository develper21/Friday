"""
System Controller Service Implementation
Implements ISystemController interface using existing SystemController
"""

from core.interfaces.controller_service import ISystemController
from assistance.controllers.system_controller import SystemController


class SystemControllerService(ISystemController):
    """System controller service implementation"""
    
    def __init__(self):
        self.system_controller = SystemController()
    
    def get_battery_info(self) -> str:
        """Get battery information"""
        return self.system_controller.get_battery_info()
    
    def get_system_status(self) -> str:
        """Get system status"""
        return self.system_controller.get_system_status()
    
    def get_time_date(self) -> str:
        """Get current time and date"""
        return self.system_controller.get_time_date()
    
    def set_volume(self, action: str) -> str:
        """Set system volume"""
        return self.system_controller.set_volume(action)
    
    def search_web(self, query: str) -> str:
        """Search web"""
        return self.system_controller.search_web(query)
    
    def power_off(self, delay: int = 0) -> bool:
        """Power off system"""
        return self.system_controller.power_off(delay)
    
    def restart(self, delay: int = 0) -> bool:
        """Restart system"""
        return self.system_controller.restart(delay)
