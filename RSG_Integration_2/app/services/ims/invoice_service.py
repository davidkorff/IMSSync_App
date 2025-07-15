import logging
from typing import Optional, Dict, Any
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class InvoiceService(BaseIMSService):
    """Service for IMS invoice operations"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("invoice_factory")
        self.auth_service = auth_service
    
    def get_invoice(self, policy_guid: UUID) -> Optional[Dict[str, Any]]:
        """Get invoice details for a policy"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.GenerateInvoice(
                quoteGuid=str(policy_guid),
                _soapheaders=self.get_header(token)
            )
            
            if response:
                invoice_data = {
                    "invoice_number": response.get("InvoiceNumber"),
                    "invoice_date": response.get("InvoiceDate"),
                    "amount_due": response.get("AmountDue"),
                    "amount_paid": response.get("AmountPaid"),
                    "balance": response.get("Balance"),
                    "line_items": response.get("LineItems", [])
                }
                logger.info(f"Retrieved invoice for policy {policy_guid}")
                return invoice_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting invoice: {e}")
            return None
    
    def get_invoice_pdf(self, policy_guid: UUID) -> Optional[bytes]:
        """Get invoice as PDF"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.GenerateInvoiceAsPDF(
                quoteGuid=str(policy_guid),
                _soapheaders=self.get_header(token)
            )
            
            if response:
                logger.info(f"Retrieved invoice PDF for policy {policy_guid}")
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting invoice PDF: {e}")
            return None