"""
Microservices package initialization
"""

from app.microservices.core import ServiceRegistry, get_service
from app.microservices.insured import InsuredService
from app.microservices.data_access import DataAccessService
from app.microservices.quote import QuoteService
from app.microservices.policy import PolicyService
from app.microservices.invoice import InvoiceService
from app.microservices.document import DocumentService
from app.microservices.producer import ProducerService

# Initialize service registry
registry = ServiceRegistry.get_instance()

# Register all microservices
def initialize_services():
    """Initialize and register all microservices"""
    
    # Register service classes for lazy instantiation
    registry.register_service_class('insured', InsuredService)
    registry.register_service_class('data_access', DataAccessService)
    registry.register_service_class('quote', QuoteService)
    registry.register_service_class('policy', PolicyService)
    registry.register_service_class('invoice', InvoiceService)
    registry.register_service_class('document', DocumentService)
    registry.register_service_class('producer', ProducerService)


# Initialize services on import
initialize_services()

# Export convenience functions and all services
__all__ = [
    'get_service',
    'ServiceRegistry',
    'InsuredService',
    'DataAccessService',
    'QuoteService',
    'PolicyService',
    'InvoiceService',
    'DocumentService',
    'ProducerService'
]