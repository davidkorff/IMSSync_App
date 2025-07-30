import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from xml.sax.saxutils import unescape

from app.services.ims.auth_service import get_auth_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSUnderwriterService:
    """Service for handling IMS Underwriter operations."""
    
    def __init__(self):
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["data_access"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
        
    def get_underwriter_by_name(self, underwriter_name: str) -> Tuple[bool, Optional[str], str]:
        """
        Get underwriter GUID by name using the getUserbyName stored procedure.
        
        Args:
            underwriter_name: Full name of the underwriter (e.g., "Christina Rentas")
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, underwriter_guid, message)
        """
        try:
            # Ensure we have a valid token
            token = self.auth_service.token
            if not token:
                return False, None, "Failed to authenticate with IMS"
            
            # Construct SOAP request for ExecuteDataSet
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>getUserbyName_WS</procedureName>
      <parameters>
        <string>fullname</string>
        <string>{self._escape_xml(underwriter_name)}</string>
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet'
            }
            
            # Make request
            url = f"{self.base_url}{self.services_env}{self.endpoint}"
            logger.info(f"Looking up underwriter: {underwriter_name}")
            logger.debug(f"SOAP Request URL: {url}")
            logger.debug(f"SOAP Request:\n{soap_request}")
            
            # Store request details for error reporting
            self._last_url = url
            self._last_soap_request = soap_request
            
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
            
            # Parse response
            return self._parse_underwriter_response(response.text, underwriter_name)
            
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
            error_msg = f"Unexpected error during underwriter lookup: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_underwriter_response(self, response_xml: str, underwriter_name: str) -> Tuple[bool, Optional[str], str]:
        """
        Parse the ExecuteDataSet response for underwriter lookup.
        
        Args:
            response_xml: The SOAP response XML string
            underwriter_name: The name that was searched
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, underwriter_guid, message)
        """
        try:
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/DataAccess'
            }
            
            # Find ExecuteDataSetResult
            result = root.find('.//ims:ExecuteDataSetResult', namespaces)
            
            if result is None:
                return False, None, "ExecuteDataSetResult not found in response"
            
            # The result contains escaped XML, need to unescape it
            result_xml = result.text
            if result_xml:
                # Unescape the XML content
                result_xml = unescape(result_xml)
                
                # Parse the inner XML
                result_root = ET.fromstring(result_xml)
                
                # Find the Table element containing UserGUID
                table = result_root.find('.//Table')
                if table is not None:
                    user_guid = table.find('UserGUID')
                    if user_guid is not None and user_guid.text:
                        underwriter_guid = user_guid.text
                        logger.info(f"Found underwriter '{underwriter_name}' with GUID: {underwriter_guid}")
                        return True, underwriter_guid, f"Found underwriter: {underwriter_name}"
                    else:
                        return False, None, f"Underwriter '{underwriter_name}' not found"
                else:
                    return False, None, f"No underwriter found with name: {underwriter_name}"
            else:
                return False, None, "No results returned from stored procedure"
                
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error processing underwriter response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def process_underwriter_from_payload(self, payload: Dict) -> Tuple[bool, Optional[str], str]:
        """
        Extract underwriter name from payload and get underwriter GUID.
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, underwriter_guid, message)
        """
        underwriter_name = payload.get("underwriter_name", "")
        
        if not underwriter_name:
            return False, None, "No underwriter name found in payload"
        
        success, guid, message = self.get_underwriter_by_name(underwriter_name)
        
        # If failed and we have debugging info, include it in the message
        if not success and (self._last_soap_request or self._last_soap_response):
            return success, guid, message
        
        return success, guid, message
    
    def _escape_xml(self, value: str) -> str:
        """Escape special XML characters."""
        if not value:
            return ""
        return (value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


# Singleton instance
_underwriter_service = None


def get_underwriter_service() -> IMSUnderwriterService:
    """Get singleton instance of underwriter service."""
    global _underwriter_service
    if _underwriter_service is None:
        _underwriter_service = IMSUnderwriterService()
    return _underwriter_service