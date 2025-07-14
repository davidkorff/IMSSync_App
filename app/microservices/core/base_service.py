"""
Base microservice class with common functionality
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

from app.services.ims_soap_client import IMSSoapClient
from app.services.ims.base_service import IMSAuthenticationManager
from app.core.config import settings
from .models import ServiceHealth, ServiceStatus, ServiceResponse
from .exceptions import ServiceError, IMSConnectionError


class ServiceConfig:
    """Configuration for a microservice"""
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        environment: Optional[str] = None,
        enable_caching: bool = True,
        cache_ttl: int = 300,
        enable_metrics: bool = True,
        enable_tracing: bool = True
    ):
        self.name = name
        self.version = version
        self.environment = environment or settings.DEFAULT_ENVIRONMENT
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.enable_metrics = enable_metrics
        self.enable_tracing = enable_tracing


class BaseMicroservice(ABC):
    """
    Base class for all microservices
    Provides common functionality like logging, health checks, and IMS connection
    """
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = logging.getLogger(f"microservice.{config.name}")
        self._start_time = datetime.now()
        self._soap_client: Optional[IMSSoapClient] = None
        self._auth_manager: Optional[IMSAuthenticationManager] = None
        self._health_status = ServiceStatus.STARTING
        self._dependencies: Dict[str, ServiceStatus] = {}
        
        # Initialize service
        self._initialize()
    
    def _initialize(self):
        """Initialize the service"""
        try:
            self.logger.info(f"Initializing {self.config.name} service v{self.config.version}")
            
            # Set up IMS connection if needed
            if self._requires_ims_connection():
                self._setup_ims_connection()
            
            # Run service-specific initialization
            self._on_initialize()
            
            self._health_status = ServiceStatus.HEALTHY
            self.logger.info(f"{self.config.name} service initialized successfully")
            
        except Exception as e:
            self._health_status = ServiceStatus.UNHEALTHY
            self.logger.error(f"Failed to initialize {self.config.name}: {str(e)}")
            raise ServiceError(f"Service initialization failed: {str(e)}")
    
    def _setup_ims_connection(self):
        """Set up IMS SOAP client and authentication"""
        try:
            # Get IMS configuration
            env_config = settings.IMS_ENVIRONMENTS.get(self.config.environment, {})
            if not env_config:
                raise ServiceError(f"IMS environment '{self.config.environment}' not configured")
            
            # Initialize SOAP client
            self._soap_client = IMSSoapClient(
                wsdl_url=env_config["wsdl_url"],
                username=env_config["username"],
                password=env_config["password"],
                company_guid=env_config.get("company_guid", "")
            )
            
            # Get authentication manager singleton
            self._auth_manager = IMSAuthenticationManager(self.config.environment)
            
        except Exception as e:
            raise IMSConnectionError(f"Failed to connect to IMS: {str(e)}")
    
    @property
    def soap_client(self) -> IMSSoapClient:
        """Get the SOAP client, ensuring it's authenticated"""
        if not self._soap_client:
            raise ServiceError("SOAP client not initialized")
        
        # Ensure authentication
        if self._auth_manager and not self._auth_manager.is_authenticated:
            self._auth_manager.authenticate()
        
        return self._soap_client
    
    def _requires_ims_connection(self) -> bool:
        """Override to indicate if service needs IMS connection"""
        return True
    
    @abstractmethod
    def _on_initialize(self):
        """Service-specific initialization - must be implemented by subclasses"""
        pass
    
    async def health_check(self) -> ServiceHealth:
        """Perform health check"""
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        # Check dependencies
        dependencies = await self._check_dependencies()
        
        # Determine overall health
        if self._health_status == ServiceStatus.UNHEALTHY:
            status = ServiceStatus.UNHEALTHY
        elif any(s != ServiceStatus.HEALTHY for s in dependencies.values()):
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.HEALTHY
        
        return ServiceHealth(
            service_name=self.config.name,
            status=status,
            version=self.config.version,
            uptime_seconds=uptime,
            last_check=datetime.now(),
            dependencies=dependencies,
            metrics=await self._get_metrics()
        )
    
    async def _check_dependencies(self) -> Dict[str, ServiceStatus]:
        """Check health of service dependencies"""
        dependencies = {}
        
        # Check IMS connection if required
        if self._requires_ims_connection():
            try:
                if self._auth_manager and self._auth_manager.is_authenticated:
                    dependencies["ims"] = ServiceStatus.HEALTHY
                else:
                    dependencies["ims"] = ServiceStatus.UNHEALTHY
            except:
                dependencies["ims"] = ServiceStatus.UNHEALTHY
        
        return dependencies
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Get service metrics - override for custom metrics"""
        return {}
    
    def _log_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log service operation"""
        log_data = {
            "service": self.config.name,
            "operation": operation,
            "environment": self.config.environment,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            log_data.update(details)
        
        self.logger.info(f"{operation}: {log_data}")
    
    def _handle_error(self, error: Exception, operation: str) -> ServiceResponse:
        """Standard error handling"""
        self.logger.error(f"Error in {operation}: {str(error)}")
        
        return ServiceResponse(
            success=False,
            error=str(error),
            metadata={
                "service": self.config.name,
                "operation": operation,
                "error_type": type(error).__name__
            }
        )
    
    async def _execute_with_retry(
        self, 
        func, 
        max_retries: int = 3, 
        retry_delay: float = 1.0,
        *args, 
        **kwargs
    ):
        """Execute function with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        raise last_error
    
    def shutdown(self):
        """Shutdown the service gracefully"""
        self.logger.info(f"Shutting down {self.config.name} service")
        self._health_status = ServiceStatus.STOPPING
        
        try:
            # Run service-specific shutdown
            self._on_shutdown()
            
            # Clean up resources
            if self._soap_client:
                # SOAP client cleanup if needed
                pass
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
        
        self._health_status = ServiceStatus.UNHEALTHY
    
    @abstractmethod
    def _on_shutdown(self):
        """Service-specific shutdown - override if needed"""
        pass