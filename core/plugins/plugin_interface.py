"""
Plugin System Interfaces
Defines abstract interfaces for plugin system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IPlugin(ABC):
    """Base plugin interface"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        """Initialize plugin with configuration"""
        pass
    
    @abstractmethod
    def execute(self, command: str, params: Dict[str, Any]) -> Optional[Any]:
        """Execute plugin command"""
        pass
    
    @abstractmethod
    def shutdown(self):
        """Shutdown plugin and cleanup resources"""
        pass


class IPluginManager(ABC):
    """Plugin manager interface"""
    
    @abstractmethod
    def load_plugin(self, plugin_path: str) -> bool:
        """Load plugin from file"""
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload plugin by name"""
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """Get loaded plugin by name"""
        pass
    
    @abstractmethod
    def list_plugins(self) -> list:
        """List all loaded plugins"""
        pass
    
    @abstractmethod
    def execute_plugin_command(self, plugin_name: str, command: str, params: Dict[str, Any]) -> Optional[Any]:
        """Execute command on specific plugin"""
        pass
