"""
Service Registry for dependency injection and service discovery
"""

import logging
from typing import Dict, Type, Optional, Any
from threading import Lock

from .base_service import BaseMicroservice
from .exceptions import ServiceNotFoundError, ServiceConfigurationError


class ServiceRegistry:
    """
    Singleton registry for managing microservice instances
    Provides dependency injection and service discovery
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger("microservice.registry")
        self._services: Dict[str, BaseMicroservice] = {}
        self._service_classes: Dict[str, Type[BaseMicroservice]] = {}
        self._service_configs: Dict[str, Any] = {}
        self._initialized = True
        
        self.logger.info("Service Registry initialized")
    
    def register_service_class(
        self, 
        name: str, 
        service_class: Type[BaseMicroservice],
        config: Optional[Any] = None
    ):
        """
        Register a service class for lazy instantiation
        
        Args:
            name: Service name
            service_class: Service class (must inherit from BaseMicroservice)
            config: Service configuration
        """
        if not issubclass(service_class, BaseMicroservice):
            raise ServiceConfigurationError(
                f"Service class {service_class.__name__} must inherit from BaseMicroservice"
            )
        
        self._service_classes[name] = service_class
        if config:
            self._service_configs[name] = config
        
        self.logger.info(f"Registered service class: {name} -> {service_class.__name__}")
    
    def register_service_instance(self, name: str, instance: BaseMicroservice):
        """
        Register a pre-instantiated service
        
        Args:
            name: Service name
            instance: Service instance
        """
        if not isinstance(instance, BaseMicroservice):
            raise ServiceConfigurationError(
                f"Service instance must inherit from BaseMicroservice"
            )
        
        self._services[name] = instance
        self.logger.info(f"Registered service instance: {name}")
    
    def get_service(self, name: str) -> BaseMicroservice:
        """
        Get a service instance by name
        Lazy instantiation if service class is registered but not instantiated
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
        """
        # Return existing instance if available
        if name in self._services:
            return self._services[name]
        
        # Try to instantiate from registered class
        if name in self._service_classes:
            self.logger.info(f"Lazy instantiating service: {name}")
            
            service_class = self._service_classes[name]
            config = self._service_configs.get(name)
            
            try:
                if config:
                    instance = service_class(config)
                else:
                    instance = service_class()
                
                self._services[name] = instance
                return instance
                
            except Exception as e:
                raise ServiceConfigurationError(
                    f"Failed to instantiate service {name}: {str(e)}"
                )
        
        raise ServiceNotFoundError(f"Service '{name}' not found in registry")
    
    def list_services(self) -> Dict[str, str]:
        """
        List all registered services
        
        Returns:
            Dict of service names to their status
        """
        services = {}
        
        # List instantiated services
        for name, instance in self._services.items():
            services[name] = f"Active ({instance.__class__.__name__})"
        
        # List registered but not instantiated services
        for name, service_class in self._service_classes.items():
            if name not in self._services:
                services[name] = f"Registered ({service_class.__name__})"
        
        return services
    
    def is_registered(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services or name in self._service_classes
    
    def shutdown_all(self):
        """Shutdown all active services"""
        self.logger.info("Shutting down all services")
        
        for name, service in self._services.items():
            try:
                self.logger.info(f"Shutting down service: {name}")
                service.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down service {name}: {str(e)}")
        
        self._services.clear()
    
    def clear(self):
        """Clear all registrations (useful for testing)"""
        self.shutdown_all()
        self._service_classes.clear()
        self._service_configs.clear()
        self.logger.info("Service registry cleared")
    
    @classmethod
    def get_instance(cls) -> 'ServiceRegistry':
        """Get the singleton instance"""
        return cls()


# Convenience function for getting the registry
def get_registry() -> ServiceRegistry:
    """Get the service registry instance"""
    return ServiceRegistry.get_instance()


# Convenience function for getting a service
def get_service(name: str) -> BaseMicroservice:
    """
    Get a service from the registry
    
    Args:
        name: Service name
        
    Returns:
        Service instance
    """
    return get_registry().get_service(name)