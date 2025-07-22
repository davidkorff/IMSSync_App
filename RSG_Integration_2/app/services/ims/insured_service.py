import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from datetime import datetime

from app.services.ims.auth_service import get_auth_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSInsuredService:
    """Service for handling IMS Insured-related operations."""
    
    def __init__(self):
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_origintest")
        self.login_env = IMS_CONFIG.get("environments", {}).get("login", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["insured_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        
    def find_insured_by_name(self, insured_name: str, city: str = "", 
                            state: str = "", zip_code: str = "") -> Tuple[bool, Optional[str], str]:
        """
        Find an insured by name and optional location details.
        
        Args:
            insured_name: Name of the insured to search for
            city: Optional city name
            state: Optional state code
            zip_code: Optional ZIP code
            
        Returns:
            Tuple[bool, Optional[str], str]: (found, insured_guid, message)
        """
        try:
            # Ensure we have a valid token
            token = self.auth_service.token
            if not token:
                return False, None, "Failed to authenticate with IMS"
            
            # Construct SOAP request
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <FindInsuredByName xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
      <insuredName>{self._escape_xml(insured_name)}</insuredName>
      <city>{self._escape_xml(city)}</city>
      <state>{self._escape_xml(state)}</state>
      <zip>{self._escape_xml(zip_code)}</zip>
    </FindInsuredByName>
  </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/InsuredFunctions/FindInsuredByName'
            }
            
            # Make request - FindInsuredByName uses /ims_origintest
            url = f"{self.base_url}{self.services_env}{self.endpoint}"
            logger.info(f"Searching for insured: {insured_name} in {city}, {state} {zip_code}")
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse response
            return self._parse_find_insured_response(response.text, insured_name)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during insured search: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_find_insured_response(self, response_xml: str, insured_name: str) -> Tuple[bool, Optional[str], str]:
        """
        Parse the FindInsuredByName response XML.
        
        Args:
            response_xml: The SOAP response XML string
            insured_name: The name that was searched
            
        Returns:
            Tuple[bool, Optional[str], str]: (found, insured_guid, message)
        """
        try:
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/InsuredFunctions'
            }
            
            # Find FindInsuredByNameResult
            result = root.find('.//ims:FindInsuredByNameResult', namespaces)
            
            if result is None:
                return False, None, "FindInsuredByNameResult not found in response"
            
            insured_guid = result.text
            
            # Check for null GUID (not found)
            if insured_guid == "00000000-0000-0000-0000-000000000000":
                return False, None, f"Insured '{insured_name}' not found in IMS"
            
            logger.info(f"Found insured '{insured_name}' with GUID: {insured_guid}")
            return True, insured_guid, f"Found insured with GUID: {insured_guid}"
            
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error processing find insured response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def process_triton_payload(self, payload: Dict) -> Tuple[bool, Optional[str], str]:
        """
        Process a Triton payload to find the insured.
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            Tuple[bool, Optional[str], str]: (found, insured_guid, message)
        """
        # Extract insured information from payload
        insured_name = payload.get("insured_name", "")
        city = payload.get("city", "")
        state = payload.get("state", "")
        zip_code = payload.get("zip", "")
        
        if not insured_name:
            return False, None, "No insured name found in payload"
        
        # Search for the insured
        return self.find_insured_by_name(insured_name, city, state, zip_code)
    
    def add_insured_with_location(self, insured_name: str, address1: str, 
                                 city: str, state: str, zip_code: str,
                                 address2: str = "") -> Tuple[bool, Optional[str], str]:
        """
        Add a new insured with location information.
        
        Args:
            insured_name: Name of the insured/corporation
            address1: Primary address line
            city: City name
            state: State code
            zip_code: ZIP code
            address2: Optional second address line
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, insured_guid, message)
        """
        try:
            # Ensure we have a valid token
            token = self.auth_service.token
            if not token:
                return False, None, "Failed to authenticate with IMS"
            
            # Construct SOAP request with hardcoded values as specified
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <AddInsuredWithLocation xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
      <insured>
        <BusinessTypeID>9</BusinessTypeID>
        <CorporationName>{self._escape_xml(insured_name)}</CorporationName>
        <NameOnPolicy>{self._escape_xml(insured_name)}</NameOnPolicy>
      </insured>
      <location>
        <LocationName>{self._escape_xml(insured_name)}</LocationName>
        <Address1>{self._escape_xml(address1)}</Address1>
        <Address2>{self._escape_xml(address2)}</Address2>
        <City>{self._escape_xml(city)}</City>
        <State>{self._escape_xml(state)}</State>
        <Zip>{self._escape_xml(zip_code)}</Zip>
        <ISOCountryCode>USA</ISOCountryCode>
        <DeliveryMethodID>1</DeliveryMethodID>
        <LocationTypeID>1</LocationTypeID>
      </location>
    </AddInsuredWithLocation>
  </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/InsuredFunctions/AddInsuredWithLocation'
            }
            
            # Make request - AddInsuredWithLocation uses /ims_one as specified
            url = f"{self.base_url}{self.login_env}{self.endpoint}"
            logger.info(f"Adding new insured: {insured_name}")
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse response
            return self._parse_add_insured_response(response.text, insured_name)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during insured creation: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_add_insured_response(self, response_xml: str, insured_name: str) -> Tuple[bool, Optional[str], str]:
        """
        Parse the AddInsuredWithLocation response XML.
        
        Args:
            response_xml: The SOAP response XML string
            insured_name: The name of the insured that was created
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, insured_guid, message)
        """
        try:
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/InsuredFunctions'
            }
            
            # Find AddInsuredWithLocationResult
            result = root.find('.//ims:AddInsuredWithLocationResult', namespaces)
            
            if result is None:
                return False, None, "AddInsuredWithLocationResult not found in response"
            
            insured_guid = result.text
            
            # Check for null GUID (creation failed)
            if not insured_guid or insured_guid == "00000000-0000-0000-0000-000000000000":
                return False, None, f"Failed to create insured '{insured_name}'"
            
            logger.info(f"Successfully created insured '{insured_name}' with GUID: {insured_guid}")
            return True, insured_guid, f"Created insured with GUID: {insured_guid}"
            
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error processing add insured response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def find_or_create_insured(self, payload: Dict) -> Tuple[bool, Optional[str], str]:
        """
        Find an existing insured or create a new one based on the payload.
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, insured_guid, message)
        """
        # Extract insured information from payload
        insured_name = payload.get("insured_name", "")
        address1 = payload.get("address_1", "")
        address2 = payload.get("address_2", "")
        city = payload.get("city", "")
        state = payload.get("state", "")
        zip_code = payload.get("zip", "")
        
        if not insured_name:
            return False, None, "No insured name found in payload"
        
        # First, try to find the insured
        logger.info(f"Attempting to find insured: {insured_name}")
        found, insured_guid, find_message = self.find_insured_by_name(
            insured_name, city, state, zip_code
        )
        
        if found:
            logger.info(f"Insured already exists: {insured_guid}")
            return True, insured_guid, f"Found existing insured: {insured_guid}"
        
        # Insured not found, create new one
        logger.info(f"Insured not found, creating new record")
        
        # Validate required fields for creation
        if not all([address1, city, state, zip_code]):
            return False, None, "Missing required location information for creating insured"
        
        # Create new insured
        success, new_guid, create_message = self.add_insured_with_location(
            insured_name, address1, city, state, zip_code, address2
        )
        
        if success:
            return True, new_guid, f"Created new insured: {new_guid}"
        else:
            return False, None, create_message
    
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
_insured_service = None


def get_insured_service() -> IMSInsuredService:
    """Get singleton instance of insured service."""
    global _insured_service
    if _insured_service is None:
        _insured_service = IMSInsuredService()
    return _insured_service