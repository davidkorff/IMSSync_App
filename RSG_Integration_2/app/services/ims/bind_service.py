import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from datetime import datetime

from app.services.ims.base_service import BaseIMSService
from config import IMS_CONFIG
import requests

logger = logging.getLogger(__name__)


class IMSBindService(BaseIMSService):
    """Service for binding quotes in IMS."""
    
    def __init__(self):
        super().__init__()
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["quote_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
    
    def bind_quote(self, quote_guid: str) -> Tuple[bool, Optional[str], str]:
        """
        Bind a quote and get the policy number.
        
        Args:
            quote_guid: The GUID of the quote to bind
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, policy_number, message)
        """
        try:
            # Get auth token
            auth_service = self._get_auth_service()
            token = auth_service.token
            
            if not token:
                return False, None, "Authentication required"
            
            # Build SOAP request
            soap_request = self._build_bind_quote_request(quote_guid, token)
            
            # Make the request
            url = f"{self.base_url}{self.services_env}{self.endpoint}"
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://tempuri.org/IMSWebServices/QuoteFunctions/BindQuote"
            }
            
            logger.info(f"Binding quote: {quote_guid}")
            logger.debug(f"SOAP Request URL: {url}")
            logger.debug(f"SOAP Request:\n{soap_request}")
            
            # Store request details for error reporting
            self._last_url = url
            self._last_soap_request = soap_request
            
            try:
                response = requests.post(
                    url,
                    data=soap_request,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Store response for error reporting
                self._last_soap_response = response.text
                
                # Check HTTP status
                response.raise_for_status()
                
                # Parse the response
                success, policy_number, message = self._parse_bind_quote_response(response.text)
                
                if success:
                    logger.info(f"Successfully bound quote {quote_guid} - Policy Number: {policy_number}")
                    return True, policy_number, f"Quote bound successfully. Policy Number: {policy_number}"
                else:
                    logger.error(f"Failed to bind quote {quote_guid}: {message}")
                    return False, None, message
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"HTTP request failed: {str(e)}"
                logger.error(error_msg)
                # Build detailed error message with SOAP details
                detailed_msg = error_msg
                if self._last_url:
                    detailed_msg += f"\n\nRequest URL: {self._last_url}"
                if self._last_soap_request:
                    detailed_msg += f"\n\nSOAP Request Sent:\n{self._last_soap_request}"
                if hasattr(e, 'response') and e.response is not None:
                    detailed_msg += f"\n\nHTTP Response Status: {e.response.status_code}"
                    detailed_msg += f"\n\nHTTP Response Body:\n{e.response.text}"
                return False, None, detailed_msg
                
        except Exception as e:
            error_msg = f"Error binding quote: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _build_bind_quote_request(self, quote_guid: str, token: str) -> str:
        """Build the SOAP request for BindQuote."""
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <BindQuote xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <quoteGuid>{quote_guid}</quoteGuid>
    </BindQuote>
  </soap:Body>
</soap:Envelope>"""
    
    def _parse_bind_quote_response(self, response_text: str) -> Tuple[bool, Optional[str], str]:
        """
        Parse the BindQuote response.
        
        Args:
            response_text: The SOAP response XML
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, policy_number, message)
        """
        try:
            # Parse the XML
            root = ET.fromstring(response_text)
            
            # Find BindQuoteResult
            bind_result = root.find('.//{http://tempuri.org/IMSWebServices/QuoteFunctions}BindQuoteResult')
            
            if bind_result is not None and bind_result.text:
                policy_number = bind_result.text.strip()
                return True, policy_number, "Bind successful"
            
            # Check for fault
            fault = root.find('.//soap:Fault', {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'})
            if fault is not None:
                fault_string = fault.find('faultstring')
                error_msg = fault_string.text if fault_string is not None else "Unknown SOAP fault"
                return False, None, f"SOAP Fault: {error_msg}"
            
            return False, None, "No BindQuoteResult found in response"
            
        except Exception as e:
            error_msg = f"Error parsing bind quote response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


# Singleton instance
_bind_service = None


def get_bind_service() -> IMSBindService:
    """Get singleton instance of bind service."""
    global _bind_service
    if _bind_service is None:
        _bind_service = IMSBindService()
    return _bind_service