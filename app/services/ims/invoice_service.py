import logging
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import IMSAuthService, get_auth_service
from .data_access_service import get_data_access_service

logger = logging.getLogger(__name__)

class InvoiceService(BaseIMSService):
    """Service for IMS invoice operations"""
    
    def __init__(self, auth_service: IMSAuthService = None):
        super().__init__("invoice_factory")
        self.auth_service = auth_service or get_auth_service()
        self.data_access_service = get_data_access_service()
    
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
    
    def get_invoice_by_params(
        self,
        invoice_num: Optional[int] = None,
        quote_guid: Optional[str] = None,
        policy_number: Optional[str] = None,
        opportunity_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Get invoice data using various parameters.
        This method uses the ryan_rptInvoice_WS stored procedure through DataAccess.
        
        Args:
            invoice_num: The invoice number
            quote_guid: The quote GUID
            policy_number: The policy number
            opportunity_id: The opportunity ID (option_id)
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, invoice_data, message)
        """
        try:
            # Ensure authentication
            auth_success, auth_message = self.auth_service.login()
            if not auth_success:
                return False, None, f"Authentication failed: {auth_message}"
            
            # If opportunity_id is provided, first look up the quote_guid
            if opportunity_id and not quote_guid:
                logger.info(f"Looking up quote by opportunity_id: {opportunity_id}")
                success, quote_info, message = self.data_access_service.get_quote_by_opportunity_id(opportunity_id)
                if success and quote_info:
                    quote_guid = quote_info.get("QuoteGuid")
                    logger.info(f"Found quote_guid {quote_guid} for opportunity_id {opportunity_id}")
                else:
                    # Try as option_id if opportunity_id lookup fails
                    try:
                        option_id_int = int(opportunity_id)
                        # Note: option_id is actually opportunity_id (naming confusion in the system)
                        success, quote_info, message = self.data_access_service.get_quote_by_opportunity_id(option_id_int)
                        if success and quote_info:
                            quote_guid = quote_info.get("QuoteGuid")
                            logger.info(f"Found quote_guid {quote_guid} for option_id {opportunity_id}")
                    except ValueError:
                        pass
            
            # If policy_number is provided and no quote_guid yet, look it up
            if policy_number and not quote_guid:
                logger.info(f"Looking up quote by policy_number: {policy_number}")
                success, quote_info, message = self.data_access_service.get_quote_by_policy_number(policy_number)
                if success and quote_info:
                    quote_guid = quote_info.get("QuoteGuid")
                    logger.info(f"Found quote_guid {quote_guid} for policy_number {policy_number}")
            
            # Build parameters for the stored procedure call
            params = []
            
            if invoice_num:
                params = ["InvoiceNum", invoice_num]
                logger.info(f"Getting invoice by InvoiceNum: {invoice_num}")
            elif quote_guid:
                params = ["QuoteGuid", quote_guid]
                logger.info(f"Getting invoice by QuoteGuid: {quote_guid}")
            elif policy_number:
                params = ["PolicyNumber", policy_number]
                logger.info(f"Getting invoice by PolicyNumber: {policy_number}")
            elif opportunity_id:
                params = ["OpportunityID", opportunity_id]
                logger.info(f"Getting invoice by OpportunityID: {opportunity_id}")
            else:
                return False, None, "No valid parameters provided for invoice lookup"
            
            # Execute the stored procedure
            success, result_xml, message = self.data_access_service.execute_dataset(
                "ryan_rptInvoice",
                params
            )
            
            if not success:
                return False, None, f"Failed to retrieve invoice: {message}"
            
            # Parse the invoice XML to JSON
            invoice_data = self.data_access_service._parse_invoice_xml_to_json(result_xml)
            
            if invoice_data:
                logger.info(f"Successfully retrieved invoice data")
                return True, invoice_data, "Invoice data retrieved successfully"
            else:
                return False, None, "No invoice data found"
                
        except Exception as e:
            error_msg = f"Error getting invoice by params: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg


# Singleton instance
_invoice_service = None


def get_invoice_service() -> InvoiceService:
    """Get singleton instance of invoice service."""
    global _invoice_service
    if _invoice_service is None:
        _invoice_service = InvoiceService()
    return _invoice_service