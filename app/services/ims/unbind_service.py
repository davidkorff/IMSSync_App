import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, Dict, Any

from app.services.ims.base_service import BaseIMSService
from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service
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
        self.data_service = get_data_access_service()
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
    
    def unbind_policy(self, quote_guid: str, keep_policy_numbers: bool = True, keep_affidavit_numbers: bool = True) -> Tuple[bool, str]:
        """
        Unbind a policy using DataAccess stored procedure.
        
        Args:
            quote_guid: The GUID of the quote to unbind
            keep_policy_numbers: Whether to keep the policy numbers
            keep_affidavit_numbers: Whether to keep affidavit numbers
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Get user guid from auth service
            user_guid = self.auth_service.user_guid
            
            if not user_guid:
                return False, "Authentication required - no user GUID available"
            
            logger.info(f"Unbinding policy for quote: {quote_guid}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "QuoteGuid", str(quote_guid),
                "UserGuid", str(user_guid),
                "KeepPolicyNumbers", "1" if keep_policy_numbers else "0",
                "KeepAffidavitNumbers", "1" if keep_affidavit_numbers else "0"
            ]
            
            # Call the stored procedure
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_UnbindPolicy",
                parameters=params
            )
            
            if not success:
                return False, f"Failed to execute unbind procedure: {message}"
            
            # Parse the result
            result_data = self._parse_unbind_procedure_result(result_xml)
            
            if result_data and result_data.get("Result") == "1":
                logger.info(f"Successfully unbound policy for quote {quote_guid}")
                return True, result_data.get("Message", "Policy unbound successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to unbind policy: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error unbinding policy: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def unbind_policy_by_option_id(self, option_id: int, keep_policy_numbers: bool = True, keep_affidavit_numbers: bool = True) -> Tuple[bool, Dict[str, Any], str]:
        """
        Unbind a policy using option ID via stored procedure.
        
        Args:
            option_id: The option ID to unbind
            keep_policy_numbers: Whether to keep the policy numbers
            keep_affidavit_numbers: Whether to keep affidavit numbers
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
        """
        try:
            # Get user guid from auth service
            user_guid = self.auth_service.user_guid
            
            if not user_guid:
                return False, {}, "Authentication required - no user GUID available"
            
            logger.info(f"Unbinding policy for option ID: {option_id}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "OptionID", str(option_id),
                "UserGuid", str(user_guid),
                "KeepPolicyNumbers", "1" if keep_policy_numbers else "0",
                "KeepAffidavitNumbers", "1" if keep_affidavit_numbers else "0"
            ]
            
            # Call the stored procedure
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_UnbindPolicy",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute unbind procedure: {message}"
            
            # Parse the result
            result_data = self._parse_unbind_procedure_result(result_xml)
            
            if result_data and result_data.get("Result") == "1":
                logger.info(f"Successfully unbound policy. QuoteGuid: {result_data.get('QuoteGuid')}, PolicyNumber: {result_data.get('PolicyNumber')}")
                return True, result_data, result_data.get("Message", "Policy unbound successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to unbind policy: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error unbinding policy by option ID: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
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
    
    def _parse_unbind_procedure_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result from Triton_UnbindPolicy_WS stored procedure.
        Handles both simple numeric results and structured results.
        
        Args:
            result_xml: The XML result from ExecuteDataSet
            
        Returns:
            Dict containing the result data or None if parsing fails
        """
        try:
            if not result_xml:
                return None
                
            # Parse the XML
            root = ET.fromstring(result_xml)
            
            # Find the first Table element (single row result)
            table = root.find('.//Table')
            if table is None:
                logger.warning("No Table element found in unbind result")
                return None
            
            # First, try to extract structured fields
            result_data = {}
            
            # Extract Result (0 or 1)
            result_elem = table.find('Result')
            if result_elem is not None and result_elem.text:
                result_data['Result'] = result_elem.text.strip()
            
            # Extract Message
            message_elem = table.find('Message')
            if message_elem is not None and message_elem.text:
                result_data['Message'] = message_elem.text.strip()
            
            # Extract QuoteGuid
            quote_guid_elem = table.find('QuoteGuid')
            if quote_guid_elem is not None and quote_guid_elem.text:
                result_data['QuoteGuid'] = quote_guid_elem.text.strip()
            
            # Extract PolicyNumber
            policy_num_elem = table.find('PolicyNumber')
            if policy_num_elem is not None and policy_num_elem.text:
                result_data['PolicyNumber'] = policy_num_elem.text.strip()
            
            # If we got structured data, return it
            if 'Result' in result_data:
                logger.debug(f"Parsed structured unbind result: {result_data}")
                return result_data
            
            # Otherwise, check for simple numeric result (legacy format)
            # Look for any child element with text content "1"
            for child in table:
                if child.text and child.text.strip() == "1":
                    logger.debug("Found simple numeric result: 1")
                    return {
                        'Result': '1',
                        'Message': 'Policy unbound successfully'
                    }
            
            # If no recognized format, log what we found
            logger.warning(f"Unrecognized result format. XML: {result_xml}")
            return None
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse unbind procedure result XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing unbind procedure result: {str(e)}")
            return None


# Singleton instance
_unbind_service = None


def get_unbind_service() -> IMSUnbindService:
    """Get singleton instance of unbind service."""
    global _unbind_service
    if _unbind_service is None:
        _unbind_service = IMSUnbindService()
    return _unbind_service