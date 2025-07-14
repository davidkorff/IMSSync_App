"""
Common exceptions for microservices
"""


class ServiceError(Exception):
    """Base exception for all service errors"""
    pass


class ServiceNotFoundError(ServiceError):
    """Raised when a requested service is not found"""
    pass


class ServiceConfigurationError(ServiceError):
    """Raised when service configuration is invalid"""
    pass


class IMSConnectionError(ServiceError):
    """Raised when IMS connection fails"""
    pass


class ValidationError(ServiceError):
    """Raised when data validation fails"""
    pass


class AuthenticationError(ServiceError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(ServiceError):
    """Raised when authorization fails"""
    pass