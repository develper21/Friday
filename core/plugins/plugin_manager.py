"""
Plugin Manager
Manages loading, unloading, and execution of plugins
"""

import importlib.util
import os
import sys
from typing import Dict, Any, Optional, List
from core.plugins.plugin_interface import IPlugin, IPluginManager
import logging

logger = logging.getLogger(__name__)


class PluginManager(IPluginManager):
    """Plugin manager implementation"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self._plugins: Dict[str, IPlugin] = {}
        self._ensure_plugins_dir()
    
    def _ensure_plugins_dir(self):
        """Ensure plugins directory exists"""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
    
    def load_plugin(self, plugin_path: str) -> bool:
        """
        Load plugin from file
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            True if loaded successfully
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location("plugin_module", plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load plugin spec from {plugin_path}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            sys.modules["plugin_module"] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, IPlugin) and attr != IPlugin:
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                logger.error(f"No IPlugin class found in {plugin_path}")
                return False
            
            # Instantiate plugin
            plugin = plugin_class()
            plugin.initialize({})
            
            # Register plugin
            self._plugins[plugin.name] = plugin
            logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_path}: {e}", exc_info=True)
            return False
    
    def load_all_plugins(self):
        """Load all plugins from plugins directory"""
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_path = os.path.join(self.plugins_dir, filename)
                self.load_plugin(plugin_path)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload plugin by name
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if unloaded successfully
        """
        if plugin_name in self._plugins:
            try:
                self._plugins[plugin_name].shutdown()
                del self._plugins[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                return False
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """
        Get loaded plugin by name
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin instance or None
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """
        List all loaded plugins
        
        Returns:
            List of plugin info dictionaries
        """
        return [
            {
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description
            }
            for plugin in self._plugins.values()
        ]
    
    def execute_plugin_command(self, plugin_name: str, command: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Execute command on specific plugin
        
        Args:
            plugin_name: Name of plugin
            command: Command to execute
            params: Command parameters
            
        Returns:
            Result from plugin execution
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.execute(command, params)
        return None
