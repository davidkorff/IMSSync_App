"""
Base IMS Service Module

This module provides the foundation for all IMS service interactions.
It handles authentication, token management, and provides common functionality
that all IMS services can inherit from.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading

from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class IMSAuthenticationManager:
    """
    Singleton class to manage IMS authentication across all services.
    Handles token caching and renewal.
    """
    _instance = None
    _lock = threading.Lock()
    
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
            
        self._tokens = {}  # Environment -> (token, expiry)
        self._soap_clients = {}  # Environment -> IMSSoapClient
        self._initialized = True
        logger.info("IMSAuthenticationManager initialized")
    
    def get_token(self, environment: str) -> str:
        """
        Get a valid token for the specified environment.
        Automatically handles token renewal if expired.
        """
        # Check if we have a valid token
        if environment in self._tokens:
            token, expiry = self._tokens[environment]
            if datetime.now() < expiry:
                return token
        
        # Token doesn't exist or has expired, get a new one
        return self._authenticate(environment)
    
    def _authenticate(self, environment: str) -> str:
        """Authenticate with IMS and store the token"""
        env_config = settings.IMS_ENVIRONMENTS.get(environment)
        if not env_config:
            raise ValueError(f"Unknown IMS environment: {environment}")
        
        # Get or create SOAP client for this environment
        if environment not in self._soap_clients:
            self._soap_clients[environment] = IMSSoapClient(env_config["config_file"])
        
        soap_client = self._soap_clients[environment]
        
        # Authenticate
        logger.info(f"Authenticating with IMS environment: {environment}")
        token = soap_client.login(env_config["username"], env_config["password"])
        
        # Store token with expiry (tokens typically last 8 hours, we'll renew after 7)
        expiry = datetime.now() + timedelta(hours=7)
        self._tokens[environment] = (token, expiry)
        
        logger.info(f"Successfully authenticated with {environment}, token expires at {expiry}")
        return token
    
    def get_soap_client(self, environment: str) -> IMSSoapClient:
        """Get the SOAP client for the specified environment"""
        # Ensure we have a valid token first
        self.get_token(environment)
        
        return self._soap_clients[environment]
    
    def invalidate_token(self, environment: str):
        """Invalidate a token (useful if we get authentication errors)"""
        if environment in self._tokens:
            del self._tokens[environment]
            logger.info(f"Invalidated token for environment: {environment}")


class BaseIMSService:
    """
    Base class for all IMS services.
    Provides common functionality like authentication and error handling.
    """
    
    def __init__(self, environment: Optional[str] = None):
        """Initialize the service with an environment"""
        self.environment = environment or settings.DEFAULT_ENVIRONMENT
        self._auth_manager = IMSAuthenticationManager()
        self._env_config = settings.IMS_ENVIRONMENTS.get(self.environment)
        
        if not self._env_config:
            raise ValueError(f"Unknown IMS environment: {self.environment}")
        
        logger.info(f"{self.__class__.__name__} initialized for environment: {self.environment}")
    
    @property
    def soap_client(self) -> IMSSoapClient:
        """Get the authenticated SOAP client"""
        return self._auth_manager.get_soap_client(self.environment)
    
    @property
    def token(self) -> str:
        """Get the current authentication token"""
        return self._auth_manager.get_token(self.environment)
    
    def _handle_soap_error(self, error: Exception, operation: str) -> None:
        """
        Handle SOAP errors with automatic retry for authentication issues
        """
        error_str = str(error)
        
        # Check if it's an authentication error
        if "token" in error_str.lower() or "authentication" in error_str.lower():
            logger.warning(f"Authentication error during {operation}, invalidating token and retrying")
            self._auth_manager.invalidate_token(self.environment)
            # The next call will automatically re-authenticate
        else:
            logger.error(f"SOAP error during {operation}: {error_str}")
            raise
    
    def _get_source_config(self, source: str) -> Dict[str, Any]:
        """Get configuration for a specific source (e.g., triton, xuber)"""
        sources = self._env_config.get("sources", {})
        source_config = sources.get(source.lower(), {})
        
        if not source_config:
            logger.warning(f"No specific configuration found for source: {source}")
            # Return empty config instead of raising error
            return {}
        
        return source_config
    
    def _log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Log an IMS operation for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "service": self.__class__.__name__,
            "operation": operation
        }
        
        if details:
            log_entry.update(details)
        
        logger.info(f"IMS Operation: {log_entry}")