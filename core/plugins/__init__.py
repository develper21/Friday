"""
Plugins Module
Contains plugin system for extensibility
"""

from .plugin_interface import IPlugin, IPluginManager
from .plugin_manager import PluginManager

__all__ = ['IPlugin', 'IPluginManager', 'PluginManager']
