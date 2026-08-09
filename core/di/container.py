"""
Dependency Injection Container
Manages service dependencies and enables loose coupling
"""

from typing import Dict, Type, Any, Callable
from inspect import signature


class DIContainer:
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register(self, interface: Type, implementation: Type, singleton: bool = True):
        """Register service implementation"""
        if singleton:
            self._services[interface] = implementation
        else:
            self._factories[interface] = implementation
    
    def register_instance(self, interface: Type, instance: Any):
        """Register pre-created instance"""
        self._singletons[interface] = instance
    
    def resolve(self, interface: Type) -> Any:
        """Resolve service with dependencies"""
        # Check if instance exists
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check if service registered
        if interface in self._services:
            return self._create_instance(self._services[interface])
        
        # Check if factory registered
        if interface in self._factories:
            return self._create_instance(self._factories[interface])
        
        raise ValueError(f"Service {interface} not registered")
    
    def _create_instance(self, cls: Type) -> Any:
        """Create instance with dependency injection"""
        sig = signature(cls.__init__)
        dependencies = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != param.empty:
                dependencies[param_name] = self.resolve(param.annotation)
        
        return cls(**dependencies)
