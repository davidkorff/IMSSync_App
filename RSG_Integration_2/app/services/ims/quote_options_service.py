import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple

from app.services.ims.auth_service import get_auth_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSQuoteOptionsService:
    """Service for handling IMS Quote Options operations."""
    
    def __init__(self):
        self.base_url = IMS_CONFIG["base_url"]
        self.endpoint = IMS_CONFIG["endpoints"]["quote_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        
    def auto_add_quote_options(self, quote_guid: str) -> Tuple[bool, Optional[Dict[str, str]], str]:
        """
        Automatically add quote options to a quote using the AutoAddQuoteOptions method.
        
        Args:
            quote_guid: GUID of the quote to add options to
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_option_info, message)
            quote_option_info contains: QuoteOptionGuid, LineGuid, LineName, CompanyLocation
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
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <AutoAddQuoteOptions xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <quoteGuid>{quote_guid}</quoteGuid>
    </AutoAddQuoteOptions>
  </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/QuoteFunctions/AutoAddQuoteOptions'
            }
            
            # Make request
            url = f"{self.base_url}{self.endpoint}"
            logger.info(f"Adding quote options for quote: {quote_guid}")
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse response
            return self._parse_quote_options_response(response.text, quote_guid)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during quote options addition: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_quote_options_response(self, response_xml: str, quote_guid: str) -> Tuple[bool, Optional[Dict[str, str]], str]:
        """
        Parse the AutoAddQuoteOptions response XML.
        
        Args:
            response_xml: The SOAP response XML string
            quote_guid: The quote GUID that was processed
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_option_info, message)
        """
        try:
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/QuoteFunctions',
                'bo': 'http://ws.mgasystems.com/BusinessObjects'
            }
            
            # Find QuoteOption element
            quote_option = root.find('.//bo:QuoteOption', namespaces)
            
            if quote_option is None:
                return False, None, "QuoteOption not found in response"
            
            # Extract quote option details
            option_info = {}
            
            # Extract QuoteOptionGuid
            option_guid = quote_option.find('bo:QuoteOptionGuid', namespaces)
            if option_guid is not None and option_guid.text:
                option_info['QuoteOptionGuid'] = option_guid.text
            
            # Extract LineGuid
            line_guid = quote_option.find('bo:LineGuid', namespaces)
            if line_guid is not None and line_guid.text:
                option_info['LineGuid'] = line_guid.text
            
            # Extract LineName
            line_name = quote_option.find('bo:LineName', namespaces)
            if line_name is not None and line_name.text:
                option_info['LineName'] = line_name.text
            
            # Extract CompanyLocation
            company_location = quote_option.find('bo:CompanyLocation', namespaces)
            if company_location is not None and company_location.text:
                option_info['CompanyLocation'] = company_location.text
            
            # Validate we got the essential GUID
            if 'QuoteOptionGuid' not in option_info:
                return False, None, "QuoteOptionGuid not found in response"
            
            logger.info(f"Successfully added quote option: {option_info.get('QuoteOptionGuid')} for quote: {quote_guid}")
            return True, option_info, f"Quote option added successfully"
            
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error processing quote options response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


# Singleton instance
_quote_options_service = None


def get_quote_options_service() -> IMSQuoteOptionsService:
    """Get singleton instance of quote options service."""
    global _quote_options_service
    if _quote_options_service is None:
        _quote_options_service = IMSQuoteOptionsService()
    return _quote_options_service