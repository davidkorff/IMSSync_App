"""
IMS Services Module

This module provides a clean, modular interface to IMS web services.
Each service is responsible for a specific domain of IMS functionality.
"""

from app.services.ims.base_service import BaseIMSService, IMSAuthenticationManager
from app.services.ims.insured_service import IMSInsuredService
from app.services.ims.producer_service import IMSProducerService
from app.services.ims.quote_service import IMSQuoteService
from app.services.ims.document_service import IMSDocumentService
from app.services.ims.data_access_service import IMSDataAccessService
from app.services.ims.policy_lifecycle_service import IMSPolicyLifecycleService
from app.services.ims.invoice_service import InvoiceService as IMSInvoiceService

__all__ = [
    'BaseIMSService',
    'IMSAuthenticationManager',
    'IMSInsuredService',
    'IMSProducerService',
    'IMSQuoteService',
    'IMSDocumentService',
    'IMSDataAccessService',
    'IMSPolicyLifecycleService',
    'IMSInvoiceService'
]