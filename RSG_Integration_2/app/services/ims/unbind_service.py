import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

from app.services.ims.base_service import BaseIMSService
from app.services.ims.auth_service import get_auth_service
from config import IMS_CONFIG
import requests

logger = logging.getLogger(__name__)


class IMSUnbindService(BaseIMSService):
    """Service for unbinding policies in IMS."""
    
    def __init__(self):
        super().__init__()
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["quote_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
    
    def unbind_policy(self, quote_guid: str, keep_policy_numbers: bool = True, keep_affidavit_numbers: bool = True) -> Tuple[bool, str]:
        """
        Unbind a policy.
        
        Args:
            quote_guid: The GUID of the quote to unbind
            keep_policy_numbers: Whether to keep the policy numbers
            keep_affidavit_numbers: Whether to keep affidavit numbers
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Get auth token and user guid
            token = self.auth_service.token
            user_guid = self.auth_service.user_guid
            
            if not token or not user_guid:
                return False, "Authentication required"
            
            # Build SOAP request
            soap_request = self._build_unbind_request(quote_guid, user_guid, keep_policy_numbers, keep_affidavit_numbers, token)
            
            # Make the request
            url = f"{self.base_url}{self.services_env}{self.endpoint}"
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://tempuri.org/IMSWebServices/QuoteFunctions/UnbindPolicy"
            }
            
            logger.info(f"Unbinding policy for quote: {quote_guid}")
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
                success, message = self._parse_unbind_response(response.text)
                
                if success:
                    logger.info(f"Successfully unbound policy for quote {quote_guid}")
                    return True, "Policy unbound successfully"
                else:
                    logger.error(f"Failed to unbind policy for quote {quote_guid}: {message}")
                    return False, message
                    
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
                return False, detailed_msg
                
        except Exception as e:
            error_msg = f"Error unbinding policy: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _build_unbind_request(self, quote_guid: str, user_guid: str, keep_policy_numbers: bool, keep_affidavit_numbers: bool, token: str) -> str:
        """Build the SOAP request for UnbindPolicy."""
        keep_policy_str = "true" if keep_policy_numbers else "false"
        keep_affidavit_str = "true" if keep_affidavit_numbers else "false"
        
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <UnbindPolicy xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <QuoteGuid>{quote_guid}</QuoteGuid>
      <UserGuid>{user_guid}</UserGuid>
      <KeepPolicyNumbers>{keep_policy_str}</KeepPolicyNumbers>
      <KeepAffidavitNumbers>{keep_affidavit_str}</KeepAffidavitNumbers>
    </UnbindPolicy>
  </soap:Body>
</soap:Envelope>"""
    
    def _parse_unbind_response(self, response_text: str) -> Tuple[bool, str]:
        """
        Parse the UnbindPolicy response.
        
        Args:
            response_text: The SOAP response XML
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Parse the XML
            root = ET.fromstring(response_text)
            
            # Find UnbindPolicyResult
            unbind_result = root.find('.//{http://tempuri.org/IMSWebServices/QuoteFunctions}UnbindPolicyResult')
            
            if unbind_result is not None:
                # Check if result is "1" (success) or "0" (failure)
                result_value = unbind_result.text.strip() if unbind_result.text else "0"
                if result_value == "1":
                    return True, "Unbind successful"
                else:
                    return False, "Unbind failed - quote may not be bound or other error occurred"
            
            # Check for fault
            fault = root.find('.//soap:Fault', {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'})
            if fault is not None:
                fault_string = fault.find('faultstring')
                error_msg = fault_string.text if fault_string is not None else "Unknown SOAP fault"
                return False, f"SOAP Fault: {error_msg}"
            
            return False, "No UnbindPolicyResult found in response"
            
        except Exception as e:
            error_msg = f"Error parsing unbind response: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Singleton instance
_unbind_service = None


def get_unbind_service() -> IMSUnbindService:
    """Get singleton instance of unbind service."""
    global _unbind_service
    if _unbind_service is None:
        _unbind_service = IMSUnbindService()
    return _unbind_service